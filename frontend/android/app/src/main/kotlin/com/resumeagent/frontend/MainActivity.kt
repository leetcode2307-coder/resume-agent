package com.resumeagent.frontend

import android.content.ContentValues
import android.os.Build
import android.os.Environment
import android.provider.MediaStore
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel
import java.io.File
import java.io.FileOutputStream

class MainActivity : FlutterActivity() {
    private val CHANNEL = "com.resumeagent.frontend/downloads"

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, CHANNEL).setMethodCallHandler { call, result ->
            if (call.method == "savePdfToDownloads") {
                val bytes = call.argument<ByteArray>("bytes")
                val filename = call.argument<String>("filename")
                
                if (bytes == null || filename == null) {
                    result.error("INVALID_ARGUMENTS", "Bytes or filename missing", null)
                    return@setMethodCallHandler
                }

                try {
                    val savedPath = saveToDownloads(bytes, filename)
                    result.success(savedPath)
                } catch (e: Exception) {
                    result.error("SAVE_FAILED", e.message, null)
                }
            } else {
                result.notImplemented()
            }
        }
    }

    private fun saveToDownloads(bytes: ByteArray, filename: String): String {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            val contentValues = ContentValues().apply {
                put(MediaStore.MediaColumns.DISPLAY_NAME, filename)
                put(MediaStore.MediaColumns.MIME_TYPE, "application/pdf")
                put(MediaStore.MediaColumns.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS)
            }
            val uri = contentResolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, contentValues)
                ?: throw Exception("Failed to create MediaStore entry")
            
            contentResolver.openOutputStream(uri)?.use { outputStream ->
                outputStream.write(bytes)
            } ?: throw Exception("Failed to open OutputStream")
            
            return "Internal storage/${Environment.DIRECTORY_DOWNLOADS}/$filename"
        } else {
            val downloadsDir = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS)
            if (!downloadsDir.exists()) {
                downloadsDir.mkdirs()
            }
            val file = File(downloadsDir, filename)
            FileOutputStream(file).use { it.write(bytes) }
            return file.absolutePath
        }
    }
}
