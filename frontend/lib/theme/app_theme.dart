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
