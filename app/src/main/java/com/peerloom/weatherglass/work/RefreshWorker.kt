package com.peerloom.weatherglass.work

import android.Manifest
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import androidx.work.Constraints
import androidx.work.CoroutineWorker
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.NetworkType
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import com.peerloom.weatherglass.R
import com.peerloom.weatherglass.data.Alert
import com.peerloom.weatherglass.data.Forecast
import com.peerloom.weatherglass.data.Prefs
import com.peerloom.weatherglass.data.Repo
import com.peerloom.weatherglass.data.Settings
import com.peerloom.weatherglass.data.freezeTonight
import com.peerloom.weatherglass.data.hourLabel
import com.peerloom.weatherglass.data.placeNow
import com.peerloom.weatherglass.data.rainSoon
import com.peerloom.weatherglass.data.tempText
import com.peerloom.weatherglass.ui.MainActivity
import com.peerloom.weatherglass.widget.Widgets
import java.util.concurrent.TimeUnit

// Background refresh for the widgets and alerts: hourly, or every 15 minutes
// while the rain-soon alert is on. Uses the place's saved coordinates and
// never asks for location in the background.
class RefreshWorker(context: Context, params: WorkerParameters) : CoroutineWorker(context, params) {
    override suspend fun doWork(): Result {
        val repo = Repo(applicationContext)
        val place = repo.prefs.selectedPlace() ?: return Result.success()
        if (place.isCurrent && place.lat == 0.0 && place.lon == 0.0) return Result.success()
        val s = repo.prefs.settings
        val f = repo.refreshIfStale(place, (if (s.rainSoonAlert) 12 else 20) * 60_000L) ?: return Result.retry()
        Widgets.updateAll(applicationContext)
        if (s.alerts) notifyNew(repo, f.alerts)
        yourAlerts(repo, f, s)
        return Result.success()
    }

    /** The alerts people switch on themselves: freeze tonight and rain soon. */
    private fun yourAlerts(repo: Repo, f: Forecast, s: Settings) {
        val now = placeNow(f.utcOffsetSeconds)
        val where = f.place.name
        if (s.freezeAlert) {
            freezeTonight(f, now, s.freezeAtC, repo.prefs.lastFreezeDate)?.let { fr ->
                repo.prefs.lastFreezeDate = now.toLocalDate().toString()
                val at = hourLabel(fr.at.toString(), s.use24h)
                notify(MINE, 2001, "Freeze tonight", "Low of ${tempText(fr.lowC, s.tempUnit)} around $at in $where.", R.drawable.wx_snow)
            }
        }
        if (s.rainSoonAlert) {
            val nowMs = System.currentTimeMillis()
            rainSoon(f, now, nowMs, repo.prefs.lastRainSoon)?.let { r ->
                repo.prefs.lastRainSoon = nowMs
                val word = if (r.snow) "Snow" else "Rain"
                val mins = (((r.minutes + 2) / 5) * 5).coerceAtLeast(5)
                notify(MINE, 2002, "$word soon", "$word starting in about $mins minutes in $where.", if (r.snow) R.drawable.wx_snow else R.drawable.wx_rain)
            }
        }
    }

    private fun notify(channel: String, id: Int, title: String, text: String, icon: Int) {
        val ctx = applicationContext
        if (ctx.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) return
        val open = PendingIntent.getActivity(
            ctx, 0, Intent(ctx, MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK),
            PendingIntent.FLAG_IMMUTABLE,
        )
        val n = NotificationCompat.Builder(ctx, channel)
            .setSmallIcon(icon).setContentTitle(title).setContentText(text)
            .setContentIntent(open).setAutoCancel(true).build()
        NotificationManagerCompat.from(ctx).notify(id, n)
    }

    private fun notifyNew(repo: Repo, alerts: List<Alert>) {
        val seen = repo.prefs.seenAlerts
        val fresh = alerts.filter { it.id !in seen }
        // Forget alerts that have ended so the seen list does not grow forever.
        repo.prefs.seenAlerts = alerts.map { it.id }.toSet()
        if (fresh.isEmpty()) return
        val ctx = applicationContext
        if (ctx.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) return
        val open = PendingIntent.getActivity(
            ctx, 0, Intent(ctx, MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK),
            PendingIntent.FLAG_IMMUTABLE,
        )
        fresh.forEach { a ->
            val n = NotificationCompat.Builder(ctx, CHANNEL)
                .setSmallIcon(R.drawable.wx_thunder)
                .setContentTitle(a.event)
                .setContentText(a.headline)
                .setStyle(NotificationCompat.BigTextStyle().bigText(a.headline))
                .setPriority(NotificationCompat.PRIORITY_HIGH)
                .setContentIntent(open)
                .setAutoCancel(true)
                .build()
            NotificationManagerCompat.from(ctx).notify(a.id.hashCode(), n)
        }
    }

    companion object {
        const val CHANNEL = "alerts"
        const val MINE = "mine"

        /** Hourly, or every 15 minutes while the rain-soon alert is on. */
        fun schedule(context: Context) {
            val minutes = if (Prefs(context).settings.rainSoonAlert) 15L else 60L
            val req = PeriodicWorkRequestBuilder<RefreshWorker>(minutes, TimeUnit.MINUTES)
                .setConstraints(Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build())
                .build()
            WorkManager.getInstance(context).enqueueUniquePeriodicWork("refresh", ExistingPeriodicWorkPolicy.UPDATE, req)
        }

        fun createChannel(context: Context) {
            val ch = NotificationChannel(CHANNEL, "Severe weather alerts", NotificationManager.IMPORTANCE_HIGH)
            ch.description = "Official warnings for your place."
            val mine = NotificationChannel(MINE, "Your alerts", NotificationManager.IMPORTANCE_DEFAULT)
            mine.description = "Freeze tonight and rain starting soon, when you switch them on in Settings."
            val nm = context.getSystemService(NotificationManager::class.java)
            nm.createNotificationChannel(ch)
            nm.createNotificationChannel(mine)
        }
    }
}
