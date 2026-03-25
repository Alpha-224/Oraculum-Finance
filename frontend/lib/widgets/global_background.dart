// lib/widgets/global_background.dart
import 'dart:math';
import 'dart:ui';
import 'package:flutter/material.dart';

class GlobalBackground extends StatefulWidget {
  const GlobalBackground({super.key});

  @override
  State<GlobalBackground> createState() => _GlobalBackgroundState();
}

class _GlobalBackgroundState extends State<GlobalBackground>
    with TickerProviderStateMixin {
  late final AnimationController bigBlob1Ctrl;
  late final AnimationController bigBlob2Ctrl;
  late final List<AnimationController> smallBlobCtrls;
  late final List<AnimationController> particleCtrls;
  final Random rnd = Random();

  late final List<_Blob> smallBlobs;
  late final List<_Particle> particles;

  @override
  void initState() {
    super.initState();

    // BIG BLOBS
    bigBlob1Ctrl = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 25),
    )..repeat(reverse: true);
    bigBlob2Ctrl = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 22),
    )..repeat(reverse: true);

    // SMALL BLOBS
    smallBlobs = List.generate(6, (_) {
      return _Blob(
        size: 40 + rnd.nextDouble() * 40,
        top: rnd.nextDouble() * 100,
        left: rnd.nextDouble() * 100,
        duration: 8 + rnd.nextDouble() * 6,
        delay: rnd.nextDouble() * 3,
      );
    });

    smallBlobCtrls = smallBlobs.map((b) {
      final ctrl = AnimationController(
        vsync: this,
        duration: Duration(seconds: b.duration.toInt()),
      );
      Future.delayed(Duration(seconds: b.delay.toInt()), () {
        ctrl.repeat(reverse: true);
      });
      return ctrl;
    }).toList();

    // PARTICLES
    particles = List.generate(10, (_) {
      return _Particle(
        top: rnd.nextDouble() * 100,
        left: rnd.nextDouble() * 100,
        duration: 6 + rnd.nextDouble() * 4,
      );
    });

    particleCtrls = particles.map((p) {
      final ctrl = AnimationController(
        vsync: this,
        duration: Duration(seconds: p.duration.toInt()),
      )..repeat(reverse: true);
      return ctrl;
    }).toList();
  }

  @override
  void dispose() {
    bigBlob1Ctrl.dispose();
    bigBlob2Ctrl.dispose();
    smallBlobCtrls.forEach((c) => c.dispose());
    particleCtrls.forEach((c) => c.dispose());
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        Container(color: const Color(0xff011F14)), // dark elegant green
        // BIG BLOBS
        AnimatedBuilder(
          animation: bigBlob1Ctrl,
          builder: (_, __) {
            final x = 0 + 120 * bigBlob1Ctrl.value;
            final y = 0 - 100 * bigBlob1Ctrl.value;
            final scale = 1 + 0.2 * bigBlob1Ctrl.value;
            return Positioned(
              top: MediaQuery.of(context).size.height * 0.05 + y,
              left: MediaQuery.of(context).size.width * 0.05 + x,
              child: Transform.scale(
                scale: scale,
                child: ImageFiltered(
                  imageFilter: ImageFilter.blur(sigmaX: 50, sigmaY: 50),
                  child: Container(
                    width: 600,
                    height: 600,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      gradient: LinearGradient(
                        colors: [
                          Colors.green.withOpacity(0.2),
                          Colors.teal.withOpacity(0.2),
                        ],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                    ),
                  ),
                ),
              ),
            );
          },
        ),
        AnimatedBuilder(
          animation: bigBlob2Ctrl,
          builder: (_, __) {
            final x = 0 - 100 * bigBlob2Ctrl.value;
            final y = 0 + 120 * bigBlob2Ctrl.value;
            final scale = 1 + 0.25 * bigBlob2Ctrl.value;
            return Positioned(
              bottom: MediaQuery.of(context).size.height * 0.1 - y,
              right: MediaQuery.of(context).size.width * 0.1 - x,
              child: Transform.scale(
                scale: scale,
                child: ImageFiltered(
                  imageFilter: ImageFilter.blur(sigmaX: 50, sigmaY: 50),
                  child: Container(
                    width: 500,
                    height: 500,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      gradient: LinearGradient(
                        colors: [
                          Colors.teal.withOpacity(0.2),
                          Colors.green.withOpacity(0.2),
                        ],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                    ),
                  ),
                ),
              ),
            );
          },
        ),

        // SMALL BLOBS
        ...smallBlobs.asMap().entries.map((e) {
          final i = e.key;
          final blob = e.value;
          return AnimatedBuilder(
            animation: smallBlobCtrls[i],
            builder: (_, __) {
              final x = 0 + 20 * smallBlobCtrls[i].value;
              final y = 0 - 30 * smallBlobCtrls[i].value;
              final opacity = 0.2 + 0.3 * smallBlobCtrls[i].value;
              return Positioned(
                top: MediaQuery.of(context).size.height * blob.top / 100 + y,
                left: MediaQuery.of(context).size.width * blob.left / 100 + x,
                child: Opacity(
                  opacity: opacity,
                  child: Container(
                    width: blob.size,
                    height: blob.size,
                    decoration: BoxDecoration(
                      color: Colors.green.withOpacity(0.1),
                      shape: BoxShape.circle,
                      // blur: use BackdropFilter for blur if needed
                    ),
                  ),
                ),
              );
            },
          );
        }),

        // PARTICLES
        ...particles.asMap().entries.map((e) {
          final i = e.key;
          final p = e.value;
          return AnimatedBuilder(
            animation: particleCtrls[i],
            builder: (_, __) {
              final y = 0 - 15 * particleCtrls[i].value;
              final opacity = 0.1 + 0.3 * particleCtrls[i].value;
              return Positioned(
                top: MediaQuery.of(context).size.height * p.top / 100 + y,
                left: MediaQuery.of(context).size.width * p.left / 100,
                child: Opacity(
                  opacity: opacity,
                  child: Container(
                    width: 2,
                    height: 2,
                    decoration: const BoxDecoration(
                      color: Color.fromARGB(50, 52, 211, 153),
                      shape: BoxShape.circle,
                    ),
                  ),
                ),
              );
            },
          );
        }),
      ],
    );
  }
}

class _Blob {
  double size;
  double top;
  double left;
  double duration;
  double delay;
  _Blob({
    required this.size,
    required this.top,
    required this.left,
    required this.duration,
    required this.delay,
  });
}

class _Particle {
  double top;
  double left;
  double duration;
  _Particle({required this.top, required this.left, required this.duration});
}
