import 'dart:math';
import 'package:flutter/material.dart';

/// Interactive simulation map with floating nodes, connecting lines,
/// and finger/touch-based collision repulsion.
class SimulationMap extends StatefulWidget {
  const SimulationMap({super.key});

  @override
  State<SimulationMap> createState() => _SimulationMapState();
}

class _Node {
  double x, y, vx, vy, size;
  _Node({required this.x, required this.y, required this.vx, required this.vy, required this.size});
}

class _SimulationMapState extends State<SimulationMap> with SingleTickerProviderStateMixin {
  final List<_Node> _nodes = [];
  final Random _rnd = Random();
  late final AnimationController _ticker;
  Offset? _touchPoint; // null when not touching

  @override
  void initState() {
    super.initState();
    for (int i = 0; i < 12; i++) {
      _nodes.add(_Node(
        x: _rnd.nextDouble() * 100,
        y: _rnd.nextDouble() * 100,
        vx: (_rnd.nextDouble() - 0.5) * 0.12,
        vy: (_rnd.nextDouble() - 0.5) * 0.12,
        size: _rnd.nextDouble() * 10 + 8,
      ));
    }
    _ticker = AnimationController(vsync: this, duration: const Duration(seconds: 1))
      ..repeat();
    _ticker.addListener(_tick);
  }

  void _tick() {
    setState(() {
      for (final node in _nodes) {
        // Repel from touch point
        if (_touchPoint != null) {
          final dx = node.x - _touchPoint!.dx;
          final dy = node.y - _touchPoint!.dy;
          final dist = sqrt(dx * dx + dy * dy);
          if (dist < 22 && dist > 0.1) {
            node.vx += dx / dist * 0.25;
            node.vy += dy / dist * 0.25;
          }
        }

        // Apply velocity with friction
        node.vx *= 0.985;
        node.vy *= 0.985;
        node.x += node.vx;
        node.y += node.vy;

        // Boundary bounce
        if (node.x < 3) { node.x = 3; node.vx = node.vx.abs() * 0.5; }
        if (node.x > 97) { node.x = 97; node.vx = -node.vx.abs() * 0.5; }
        if (node.y < 3) { node.y = 3; node.vy = node.vy.abs() * 0.5; }
        if (node.y > 97) { node.y = 97; node.vy = -node.vy.abs() * 0.5; }
      }
    });
  }

  @override
  void dispose() {
    _ticker.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      behavior: HitTestBehavior.opaque,
      onPanStart: (d) => _updateTouch(context, d.localPosition),
      onPanUpdate: (d) => _updateTouch(context, d.localPosition),
      onPanEnd: (_) => setState(() => _touchPoint = null),
      onTapDown: (d) => _updateTouch(context, d.localPosition),
      onTapUp: (_) => setState(() => _touchPoint = null),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(20),
        child: Container(
          decoration: BoxDecoration(
            border: Border.all(color: Colors.tealAccent.withOpacity(0.15)),
            borderRadius: BorderRadius.circular(20),
          ),
          child: CustomPaint(
            painter: _SimPainter(nodes: _nodes, touchPoint: _touchPoint),
            child: const SizedBox.expand(),
          ),
        ),
      ),
    );
  }

  void _updateTouch(BuildContext context, Offset local) {
    final box = context.findRenderObject() as RenderBox?;
    if (box == null) return;
    final size = box.size;
    setState(() {
      _touchPoint = Offset(
        (local.dx / size.width) * 100,
        (local.dy / size.height) * 100,
      );
    });
  }
}

class _SimPainter extends CustomPainter {
  final List<_Node> nodes;
  final Offset? touchPoint;

  _SimPainter({required this.nodes, this.touchPoint});

  @override
  void paint(Canvas canvas, Size size) {
    final linePaint = Paint()
      ..color = const Color.fromRGBO(52, 211, 153, 0.2)
      ..strokeWidth = 1.2;

    // Draw connections
    for (int i = 0; i < nodes.length; i++) {
      for (int j = i + 1; j < nodes.length; j++) {
        final dx = nodes[i].x - nodes[j].x;
        final dy = nodes[i].y - nodes[j].y;
        final dist = sqrt(dx * dx + dy * dy);
        if (dist < 38) {
          final opacity = ((38 - dist) / 38 * 0.35).clamp(0.0, 0.35);
          linePaint.color = Color.fromRGBO(52, 211, 153, opacity);
          canvas.drawLine(
            Offset(nodes[i].x / 100 * size.width, nodes[i].y / 100 * size.height),
            Offset(nodes[j].x / 100 * size.width, nodes[j].y / 100 * size.height),
            linePaint,
          );
        }
      }
    }

    // Draw nodes
    for (final node in nodes) {
      final center = Offset(node.x / 100 * size.width, node.y / 100 * size.height);
      final r = node.size / 2;

      // Glow
      final glowPaint = Paint()
        ..color = const Color.fromRGBO(52, 211, 153, 0.12)
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 8);
      canvas.drawCircle(center, r + 4, glowPaint);

      // Core
      final corePaint = Paint()
        ..shader = const LinearGradient(
          colors: [Color(0xFF34D399), Color(0xFF14B8A6)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ).createShader(Rect.fromCircle(center: center, radius: r));
      canvas.drawCircle(center, r, corePaint);
    }

    // Touch indicator
    if (touchPoint != null) {
      final tp = Offset(touchPoint!.dx / 100 * size.width, touchPoint!.dy / 100 * size.height);
      final touchPaint = Paint()
        ..color = const Color.fromRGBO(52, 211, 153, 0.08)
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 12);
      canvas.drawCircle(tp, 30, touchPaint);
    }
  }

  @override
  bool shouldRepaint(covariant _SimPainter oldDelegate) => true;
}
