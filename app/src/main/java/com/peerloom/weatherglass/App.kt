package com.peerloom.weatherglass

import android.app.Application
import com.peerloom.weatherglass.work.RefreshWorker

class App : Application() {
    override fun onCreate() {
        super.onCreate()
        RefreshWorker.createChannel(this)
    }
}
