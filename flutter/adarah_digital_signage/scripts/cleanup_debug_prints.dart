#!/usr/bin/env dart

import 'dart:io';
import 'dart:convert';

/// Script to remove debug print statements from Flutter project
void main() async {
  print('🧹 Starting Flutter code cleanup...\n');

  final libDir = Directory('lib');
  if (!await libDir.exists()) {
    print('❌ lib directory not found');
    exit(1);
  }

  var totalFilesProcessed = 0;
  var totalPrintsRemoved = 0;

  await for (final FileSystemEntity entity in libDir.list(recursive: true)) {
    if (entity is File && entity.path.endsWith('.dart')) {
      final result = await cleanupFile(entity);
      if (result > 0) {
        totalPrintsRemoved += result;
        print('✅ ${entity.path}: Removed $result debug prints');
      }
      totalFilesProcessed++;
    }
  }

  print('\n🎉 Cleanup completed!');
  print('📊 Files processed: $totalFilesProcessed');
  print('🗑️  Debug prints removed: $totalPrintsRemoved');
}

/// Clean up a single Dart file
Future<int> cleanupFile(File file) async {
  try {
    final content = await file.readAsString();
    final lines = content.split('\n');
    final cleanedLines = <String>[];
    var removedCount = 0;

    for (var line in lines) {
      // Skip debug print statements
      if (line.trim().startsWith("print('DEBUG:") ||
          line.trim().startsWith('print("DEBUG:') ||
          line.trim().startsWith("print('debug:") ||
          line.trim().startsWith('print("debug:') ||
          line.trim().startsWith("debugPrint('DEBUG:") ||
          line.trim().startsWith('debugPrint("DEBUG:')) {
        removedCount++;
        continue;
      }

      // Clean up other debug patterns
      var cleanedLine = line;
      
      // Simple check for debug print patterns
      if (line.contains("print('DEBUG:") || 
          line.contains('print("DEBUG:') ||
          line.contains("debugPrint('DEBUG:") || 
          line.contains('debugPrint("DEBUG:')) {
        removedCount++;
        continue;
      }

      cleanedLines.add(cleanedLine);
    }

    if (removedCount > 0) {
      await file.writeAsString(cleanedLines.join('\n'));
    }

    return removedCount;
  } catch (e) {
    print('❌ Error processing ${file.path}: $e');
    return 0;
  }
}