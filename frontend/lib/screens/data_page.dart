import 'package:flutter/material.dart';
import 'manual_entry_page.dart';
import 'document_upload_page.dart';
import '../widgets/glass_container.dart';

class DataPage extends StatelessWidget {
  const DataPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.transparent, // show background
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            children: [
              // TOP HALF: Manual Entry
              Expanded(
                child: GestureDetector(
                  onTap: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                          builder: (_) => const ManualEntryPage()),
                    );
                  },
                  child: GlassContainer(
                    margin: const EdgeInsets.only(bottom: 16),
                    child: Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.edit_note_rounded,
                              size: 80, color: Colors.tealAccent),
                          const SizedBox(height: 12),
                          const Text(
                            'Manual Entry',
                            style: TextStyle(
                              fontSize: 24,
                              fontWeight: FontWeight.bold,
                              color: Colors.white,
                              letterSpacing: 1.5,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),

              // BOTTOM HALF: Document Upload
              Expanded(
                child: GestureDetector(
                  onTap: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                          builder: (_) => const DocumentUploadPage()),
                    );
                  },
                  child: GlassContainer(
                    child: Center(
                      child: Stack(
                        alignment: Alignment.center,
                        clipBehavior: Clip.none,
                        children: [
                          Icon(Icons.camera_alt,
                              size: 80, color: Colors.white),
                          Positioned(
                            bottom: 10,
                            left: 20,
                            child: Icon(Icons.arrow_upward,
                                size: 24, color: Colors.white),
                          ),
                          Positioned(
                            bottom: -35,
                            child: const Text(
                              'Document Upload',
                              style: TextStyle(
                                fontSize: 24,
                                fontWeight: FontWeight.bold,
                                color: Colors.white,
                                letterSpacing: 1.5,
                              ),
                            ),
                          )
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
