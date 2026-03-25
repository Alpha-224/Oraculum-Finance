import 'package:flutter/material.dart';

class DocumentUploadPage extends StatelessWidget {
  const DocumentUploadPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.transparent, // Uses global background
      appBar: AppBar(
        title: const Text('Upload Document', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, letterSpacing: 1.5)),
        backgroundColor: Colors.transparent,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.white),
      ),
      body: GestureDetector(
        behavior: HitTestBehavior.opaque,
        onTap: () {
          // Placeholder for triggering native file picker popup
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Opening document picker...'),
              backgroundColor: Colors.teal,
            ),
          );
        },
        child: SizedBox.expand(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.upload_file, size: 100, color: Colors.white.withOpacity(0.5)),
              const SizedBox(height: 24),
              Text(
                'Tap anywhere to upload a document',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                  color: Colors.white.withOpacity(0.7),
                  letterSpacing: 1.2,
                ),
              ),
              const SizedBox(height: 16),
              Text(
                'Supported formats: PDF, JPG, PNG',
                style: TextStyle(
                  fontSize: 16,
                  color: Colors.white.withOpacity(0.4),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
