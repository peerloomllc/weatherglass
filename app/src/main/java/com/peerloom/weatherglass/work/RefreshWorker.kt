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
import com.peerloom.weatherglass.data.Repo
import com.peerloom.weatherglass.ui.MainActivity
import com.peerloom.weatherglass.widget.Widgets
import java.util.concurrent.TimeUnit

// Hourly refresh for the widgets and alerts. Uses the place's saved
// coordinates and never asks for location in the background.
class RefreshWorker(context: Context, params: WorkerParameters) : CoroutineWorker(context, params) {
    override suspend fun doWork(): Result {
        val repo = Repo(applicationContext)
        val place = repo.prefs.selectedPlace() ?: return Result.success()
        if (place.isCurrent && place.lat == 0.0 && place.lon == 0.0) return Result.success()
        val f = repo.refreshIfStale(place, 20 * 60_000) ?: return Result.retry()
        Widgets.updateAll(applicationContext)
        if (repo.prefs.settings.alerts) notifyNew(repo, f.alerts)
        return Result.success()
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

        fun schedule(context: Context) {
            val req = PeriodicWorkRequestBuilder<RefreshWorker>(1, TimeUnit.HOURS)
                .setConstraints(Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build())
                .build()
            WorkManager.getInstance(context).enqueueUniquePeriodicWork("refresh", ExistingPeriodicWorkPolicy.KEEP, req)
        }

        fun createChannel(context: Context) {
            val ch = NotificationChannel(CHANNEL, "Severe weather alerts", NotificationManager.IMPORTANCE_HIGH)
            ch.description = "Official warnings for your place. The only notifications Weatherglass sends."
            context.getSystemService(NotificationManager::class.java).createNotificationChannel(ch)
        }
    }
}
