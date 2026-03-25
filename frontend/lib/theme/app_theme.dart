import 'package:flutter/material.dart';

/// Centralized risk-label and action-label color/icon helpers.
/// Used consistently across dashboard, simulation, and account pages.

Color riskColor(String riskLabel) {
  switch (riskLabel) {
    case 'LOW_RISK':
      return Colors.greenAccent;
    case 'MODERATE_RISK':
      return Colors.amberAccent;
    case 'HIGH_RISK':
      return Colors.orangeAccent;
    case 'CRITICAL_RISK':
      return Colors.redAccent;
    default:
      return Colors.grey;
  }
}

String riskEmoji(String riskLabel) {
  switch (riskLabel) {
    case 'LOW_RISK':
      return '✅';
    case 'MODERATE_RISK':
      return '⚠️';
    case 'HIGH_RISK':
      return '🔶';
    case 'CRITICAL_RISK':
      return '🔴';
    default:
      return '❓';
  }
}

String riskText(String riskLabel) {
  switch (riskLabel) {
    case 'LOW_RISK':
      return 'Low Risk';
    case 'MODERATE_RISK':
      return 'Moderate Risk';
    case 'HIGH_RISK':
      return 'High Risk';
    case 'CRITICAL_RISK':
      return 'Critical Risk';
    default:
      return 'Unknown';
  }
}

Color actionColor(String label) {
  switch (label) {
    case 'PAY_NOW':
      return Colors.redAccent;
    case 'PAY_SCHEDULED':
      return Colors.greenAccent;
    case 'PARTIAL':
      return Colors.orangeAccent;
    case 'DELAY':
    case 'NEGOTIATE':
      return Colors.amberAccent;
    default:
      return Colors.grey;
  }
}

IconData actionIcon(String label) {
  switch (label) {
    case 'PAY_NOW':
      return Icons.warning_rounded;
    case 'PAY_SCHEDULED':
      return Icons.check_circle_outline;
    case 'PARTIAL':
      return Icons.pie_chart_outline;
    case 'DELAY':
      return Icons.schedule;
    case 'NEGOTIATE':
      return Icons.handshake_outlined;
    default:
      return Icons.help_outline;
  }
}

String actionText(String label) {
  switch (label) {
    case 'PAY_NOW':
      return 'Pay Now';
    case 'PAY_SCHEDULED':
      return 'Scheduled';
    case 'PARTIAL':
      return 'Partial';
    case 'DELAY':
      return 'Defer';
    case 'NEGOTIATE':
      return 'Negotiate';
    default:
      return label;
  }
}

/// Explanations for each action label — shown on long press.
String actionExplanation(String label) {
  switch (label) {
    case 'PAY_NOW':
      return 'This obligation must be settled immediately — it is due within 3 days. Delaying further will incur penalties or damage vendor relationships.';
    case 'PAY_SCHEDULED':
      return 'This payment is on track. It will be paid on the scheduled due date as part of normal operations — no action needed right now.';
    case 'PARTIAL':
      return 'Cash is tight. The engine recommends negotiating a partial payment with this vendor to preserve cash flow while maintaining the relationship.';
    case 'DELAY':
      return 'This obligation is safe to defer. The vendor or creditor is flexible enough to accept a delayed payment without significant consequences.';
    case 'NEGOTIATE':
      return 'The vendor has flexible terms. Proactively renegotiating — perhaps extending the deadline or adjusting the amount — is recommended.';
    default:
      return 'Action details unavailable.';
  }
}

/// Shows a themed bottom sheet explaining what an action label means.
void showActionTooltip(BuildContext context, String label) {
  showModalBottomSheet(
    context: context,
    backgroundColor: Colors.transparent,
    builder: (_) => Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: const Color(0xff0a2a1e),
        borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
        border: Border.all(color: actionColor(label).withOpacity(0.3)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(actionIcon(label), color: actionColor(label), size: 22),
              const SizedBox(width: 10),
              Text(
                actionText(label),
                style: TextStyle(color: actionColor(label), fontSize: 18, fontWeight: FontWeight.bold),
              ),
            ],
          ),
          const SizedBox(height: 14),
          Text(
            actionExplanation(label),
            style: const TextStyle(color: Colors.white70, fontSize: 14, height: 1.5),
          ),
          const SizedBox(height: 16),
        ],
      ),
    ),
  );
}
