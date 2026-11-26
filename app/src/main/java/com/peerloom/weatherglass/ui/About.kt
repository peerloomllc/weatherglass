package com.peerloom.weatherglass.ui

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.widget.Toast
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

// The About page and the one-time donation reminder, matching the other
// PeerLoom apps (PearList, PearOffice) minus their peer-to-peer parts.

private const val LIGHTNING_ADDRESS = "peerloomllc@strike.me"
private const val STRIKE_TIP_URL = "https://strike.me/peerloomllc/"
private const val BTC_ONCHAIN_ADDRESS = "bc1q0kksenz3j4u9ppe6f4krclvzwxk7sjy00cc9cf"
private const val BUYMEACOFFEE_URL = "https://buymeacoffee.com/peerloomllc"
private const val CRASH_COURSE_URL = "https://nakamotoinstitute.org/crash-course/"
private const val EMAIL = "peerloomllc@proton.me"
private const val ISSUES_URL = "https://github.com/peerloomllc/weatherglass/issues"
private const val SITE_URL = "https://peerloomllc.com/"

private val WALLETS = listOf(
    Triple("Strike", "Simple Lightning payments", "https://strike.me"),
    Triple("Cash App", "Send Bitcoin via Lightning", "https://cash.app"),
    Triple("Wallet of Satoshi", "Beginner-friendly Lightning wallet", "https://walletofsatoshi.com"),
    Triple("Phoenix", "Self-custodial Lightning wallet", "https://phoenix.acinq.co"),
)

private val CREDITS = listOf(
    Triple("Open-Meteo", "CC BY 4.0", "Forecasts, 15-minute rain and city search"),
    Triple("US National Weather Service", "Public domain", "Severe weather alerts"),
    Triple("Jetpack Compose, Glance, WorkManager", "Apache 2.0", "Screens, widgets and background refresh"),
    Triple("kotlinx.serialization", "Apache 2.0", "Reading the forecast data"),
    Triple("Blender", "GPL", "Used to make the skin art (not part of the app)"),
)

private fun open(context: Context, url: String) {
    runCatching { context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)) }
}

private fun copy(context: Context, label: String, text: String) {
    context.getSystemService(ClipboardManager::class.java).setPrimaryClip(ClipData.newPlainText(label, text))
    Toast.makeText(context, "Copied", Toast.LENGTH_SHORT).show()
}

private fun hasLightningWallet(context: Context) =
    Intent(Intent.ACTION_VIEW, Uri.parse("lightning:test")).resolveActivity(context.packageManager) != null

/** The About page. [startOn] opens one section first ("support" from the donation reminder). */
@Composable
fun AboutSheet(startOn: String? = null, onDismiss: () -> Unit) = Sheet(onDismiss) {
    val context = LocalContext.current
    var openId by rememberSaveable { mutableStateOf(startOn) }
    var btc by remember { mutableStateOf(false) }
    val version = remember {
        runCatching { context.packageManager.getPackageInfo(context.packageName, 0).versionName }.getOrNull() ?: "unknown"
    }
    fun toggle(id: String) { openId = if (openId == id) null else id }

    Column(Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(10.dp)) {
        Column(Modifier.fillMaxWidth(), horizontalAlignment = Alignment.CenterHorizontally) {
            T("Weatherglass", 24.sp, weight = FontWeight.Medium)
            T("Simple weather. No ads, no accounts, no tracking.", 14.sp, look.subtle, align = TextAlign.Center)
            T("Version $version", 12.sp, look.subtle)
        }

        AboutSection("How it works", openId == "how", { toggle("how") }) {
            T(
                "Your phone asks Open-Meteo for the forecast and the US National Weather Service for alerts, " +
                    "directly. There is no Weatherglass server in between, no account and no tracking. Your " +
                    "location is only sent to them to get your forecast, and only roughly.",
                14.sp,
            )
        }

        AboutSection("Support development", openId == "support", { toggle("support") }) {
            T("Weatherglass is free, with no ads, accounts or subscriptions. If you get value from it, please consider returning value.", 14.sp)
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                Button("⚡ BTC ⚡", primary = true, modifier = Modifier.weight(1f)) { btc = true }
                Button("$ USD $", modifier = Modifier.weight(1f)) { open(context, BUYMEACOFFEE_URL) }
            }
        }

        AboutSection("Learn about Bitcoin", openId == "bitcoin", { toggle("bitcoin") }) {
            T("New to Bitcoin? The Satoshi Nakamoto Institute has a free, short crash course on how Bitcoin works and why it matters.", 14.sp)
            Button("Bitcoin crash course ↗") { open(context, CRASH_COURSE_URL) }
        }

        AboutSection("Share the app", openId == "share", { toggle("share") }) {
            T("Know someone who wants a simple weather app with no ads, and widgets and skins they can make their own? Tell them about Weatherglass.", 14.sp)
            Button("Share Weatherglass") {
                val text = "Check out Weatherglass - a simple weather app with widgets and skins, no ads or accounts.\n\n$SITE_URL"
                val send = Intent(Intent.ACTION_SEND).setType("text/plain").putExtra(Intent.EXTRA_SUBJECT, "Weatherglass").putExtra(Intent.EXTRA_TEXT, text)
                context.startActivity(Intent.createChooser(send, "Share Weatherglass").addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
            }
        }

        AboutSection("Contact", openId == "contact", { toggle("contact") }) {
            T("Questions, ideas or something not working? Write to us.", 14.sp)
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                Button("Email us", modifier = Modifier.weight(1f)) { open(context, "mailto:$EMAIL?subject=%5BWeatherglass%5D%20Feedback") }
                Button("Report a problem", modifier = Modifier.weight(1f)) { open(context, ISSUES_URL) }
            }
        }

        AboutSection("Credits", openId == "credits", { toggle("credits") }) {
            T("Weatherglass is built on these, used under their licenses.", 14.sp)
            CREDITS.forEach { (name, licence, use) ->
                Column {
                    T("$name  ·  $licence", 14.sp, weight = FontWeight.Medium)
                    T(use, 13.sp, look.subtle)
                }
            }
        }

        Spacer(Modifier.height(4.dp))
        T("© PeerLoom LLC", 12.sp, look.subtle, modifier = Modifier.fillMaxWidth(), align = TextAlign.Center)
    }
    if (btc) BtcSheet { btc = false }
}

@Composable
private fun AboutSection(title: String, open: Boolean, onToggle: () -> Unit, content: @Composable () -> Unit) {
    Column(Modifier.fillMaxWidth().clip(RoundedCornerShape(look.skin.corner.dp.coerceAtMost(16.dp))).background(look.card)) {
        Row(
            Modifier.fillMaxWidth().clickable(onClick = onToggle).padding(horizontal = 16.dp, vertical = 14.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            T(look.label(title), 15.sp, weight = FontWeight.Medium, modifier = Modifier.weight(1f))
            T(if (open) "−" else "+", 20.sp, look.subtle)
        }
        AnimatedVisibility(open) {
            Column(Modifier.padding(start = 16.dp, end = 16.dp, bottom = 16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                content()
            }
        }
    }
}

/** Ways to give in Bitcoin: open a Lightning wallet, copy the address, pay in a browser or on-chain. */
@Composable
private fun BtcSheet(onDismiss: () -> Unit) = Sheet(onDismiss) {
    val context = LocalContext.current
    val wallet = remember { hasLightningWallet(context) }
    Column(Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(10.dp)) {
        T("⚡ Bitcoin Lightning ⚡", 20.sp, weight = FontWeight.Medium, modifier = Modifier.fillMaxWidth(), align = TextAlign.Center)
        T("Support Weatherglass with Bitcoin over Lightning (fast and low-fee) or on-chain.", 14.sp)
        if (wallet) {
            Button("Open in your Lightning wallet", primary = true) { open(context, "lightning:$LIGHTNING_ADDRESS") }
            T("or use another method:", 13.sp, look.subtle)
        }
        CopyRow("Lightning address", LIGHTNING_ADDRESS, "Paste into any Lightning, ecash or web wallet.")
        Button("Show a QR code or pay in a browser") { open(context, STRIKE_TIP_URL) }
        T("Scan it from another device.", 12.sp, look.subtle)
        if (BTC_ONCHAIN_ADDRESS.isNotEmpty()) {
            CopyRow("On-chain Bitcoin", BTC_ONCHAIN_ADDRESS, "Fees are higher on-chain, so Lightning is cheaper for small amounts.")
        }
        if (!wallet) {
            T(look.label("No Lightning wallet yet?"), 15.sp, weight = FontWeight.Medium)
            WALLETS.forEach { (name, what, url) ->
                Column(Modifier.fillMaxWidth().clip(RoundedCornerShape(10.dp)).clickable { open(context, url) }.padding(vertical = 6.dp)) {
                    T("$name ↗", 14.sp, weight = FontWeight.Medium)
                    T(what, 13.sp, look.subtle)
                }
            }
            T("After installing, come back here and tap BTC again.", 13.sp, look.subtle)
        }
    }
}

@Composable
private fun CopyRow(label: String, value: String, hint: String) {
    val context = LocalContext.current
    Column(Modifier.fillMaxWidth().clip(RoundedCornerShape(12.dp)).background(look.card).clickable { copy(context, label, value) }.padding(12.dp)) {
        T(look.label(label), 13.sp, look.subtle)
        T(value, 14.sp, weight = FontWeight.Medium)
        T("Tap to copy. $hint", 12.sp, look.subtle)
    }
}

/** The one-time "Enjoying Weatherglass?" note, two weeks after first use. */
@Composable
fun DonationReminder(onDonate: () -> Unit, onClose: () -> Unit) {
    AlertDialog(
        onDismissRequest = onClose,
        containerColor = look.bgTop,
        title = { T("⚡ Enjoying Weatherglass?", 20.sp, weight = FontWeight.Medium) },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                T("Weatherglass is free, with no ads, accounts or subscriptions. If you get value from it, please consider returning value to support development.", 14.sp)
                T("I already donated", 13.sp, look.subtle, modifier = Modifier.clickable(onClick = onClose))
            }
        },
        confirmButton = { Button("Donate", primary = true) { onDonate() } },
        dismissButton = { Button("Maybe later") { onClose() } },
    )
}
