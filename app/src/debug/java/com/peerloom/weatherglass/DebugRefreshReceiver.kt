package com.peerloom.weatherglass

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkManager
import com.peerloom.weatherglass.work.RefreshWorker

// Debug builds only: run the hourly refresh now, for testing widgets and
// alert notifications without waiting an hour.
//   adb shell am broadcast -n com.peerloom.weatherglass.debug/com.peerloom.weatherglass.DebugRefreshReceiver
class DebugRefreshReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        WorkManager.getInstance(context).enqueue(OneTimeWorkRequestBuilder<RefreshWorker>().build())
    }
}
