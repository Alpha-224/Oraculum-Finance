// ─── Health Response ───

class HealthResponse {
  final String status;
  final bool masterJsonExists;
  final String lastUpdated;
  final Map<String, int> recordCounts;

  HealthResponse.fromJson(Map<String, dynamic> json)
      : status = json['status'] ?? 'unknown',
        masterJsonExists = json['master_json_exists'] ?? false,
        lastUpdated = json['last_updated'] ?? '',
        recordCounts = (json['record_counts'] as Map<String, dynamic>?)?.map(
              (k, v) => MapEntry(k, (v as num).toInt()),
            ) ?? {};
}

// ─── Decision Response ───

class DecisionResponse {
  final String generatedAt;
  final int horizonDays;
  final double openingBalance;
  final Timeline timeline;
  final double survivalProbability;
  final String riskLabel;
  final List<Strategy> strategies;
  final ObligationSummary obligationSummary;
  final Metadata metadata;

  DecisionResponse.fromJson(Map<String, dynamic> json)
      : generatedAt = json['generated_at'],
        horizonDays = json['horizon_days'],
        openingBalance = (json['opening_balance'] as num).toDouble(),
        timeline = Timeline.fromJson(json['timeline']),
        survivalProbability = (json['survival_probability'] as num).toDouble(),
        riskLabel = json['risk_label'],
        strategies = (json['strategies'] as List).map((e) => Strategy.fromJson(e)).toList(),
        obligationSummary = ObligationSummary.fromJson(json['obligation_summary']),
        metadata = Metadata.fromJson(json['metadata']);
}

// ─── Timeline ───

class Timeline {
  final List<String> dates;
  final List<double> balances;
  final double minimumCash;
  final int? firstBreachDay;
  final double totalInflows;
  final double totalOutflows;
  final double netPosition;

  Timeline.fromJson(Map<String, dynamic> json)
      : dates = List<String>.from(json['dates']),
        balances = (json['balances'] as List).map((e) => (e as num).toDouble()).toList(),
        minimumCash = (json['minimum_cash'] as num).toDouble(),
        firstBreachDay = json['first_breach_day'],
        totalInflows = (json['total_inflows'] as num).toDouble(),
        totalOutflows = (json['total_outflows'] as num).toDouble(),
        netPosition = (json['net_position'] as num).toDouble();
}

// ─── Strategy ───

class Strategy {
  final String name;
  final String description;
  final double totalPayments;
  final double totalDeferred;
  final double totalLateFees;
  final double objectiveScore;
  final double survivalProbability;
  final String riskLabel;
  final RiskMetrics riskMetrics;
  final List<ActionDecision> actions;

  Strategy.fromJson(Map<String, dynamic> json)
      : name = json['name'],
        description = json['description'],
        totalPayments = (json['total_payments'] as num).toDouble(),
        totalDeferred = (json['total_deferred'] as num).toDouble(),
        totalLateFees = (json['total_late_fees'] as num).toDouble(),
        objectiveScore = (json['objective_score'] as num).toDouble(),
        survivalProbability = (json['survival_probability'] as num).toDouble(),
        riskLabel = json['risk_label'],
        riskMetrics = RiskMetrics.fromJson(json['risk_metrics']),
        actions = (json['actions'] as List).map((e) => ActionDecision.fromJson(e)).toList();
}

// ─── Action ───

class ActionDecision {
  final String obligationId;
  final String vendor;
  final double amount;
  final double paidAmount;
  final double paidFraction;
  final String actionLabel;
  final String dueDate;
  final String reasoning;

  ActionDecision.fromJson(Map<String, dynamic> json)
      : obligationId = json['obligation_id'],
        vendor = json['vendor'],
        amount = (json['amount'] as num).toDouble(),
        paidAmount = (json['paid_amount'] as num).toDouble(),
        paidFraction = (json['paid_fraction'] as num).toDouble(),
        actionLabel = json['action_label'],
        dueDate = json['due_date'],
        reasoning = json['reasoning'];
}

// ─── Risk Metrics ───

class RiskMetrics {
  final double meanEndingBalance;
  final double p10EndingBalance;
  final double p90EndingBalance;
  final double expectedShortfall;

  RiskMetrics.fromJson(Map<String, dynamic> json)
      : meanEndingBalance = (json['mean_ending_balance'] as num).toDouble(),
        p10EndingBalance = (json['p10_ending_balance'] as num).toDouble(),
        p90EndingBalance = (json['p90_ending_balance'] as num).toDouble(),
        expectedShortfall = (json['expected_shortfall'] as num).toDouble();
}

// ─── Obligation Summary ───

class ObligationSummary {
  final int totalCount;
  final double totalAmount;
  final int criticalCount;
  final int overdueCount;
  final Map<String, ActionBucket> byActionLabel;

  ObligationSummary.fromJson(Map<String, dynamic> json)
      : totalCount = json['total_count'],
        totalAmount = (json['total_amount'] as num).toDouble(),
        criticalCount = json['critical_count'],
        overdueCount = json['overdue_count'],
        byActionLabel = (json['by_action_label'] as Map<String, dynamic>).map(
          (k, v) => MapEntry(k, ActionBucket.fromJson(v)),
        );
}

class ActionBucket {
  final int count;
  final double amount;

  ActionBucket.fromJson(Map<String, dynamic> json)
      : count = json['count'],
        amount = (json['amount'] as num).toDouble();
}

// ─── Metadata ───

class Metadata {
  final String masterJsonLastUpdated;
  final int transactionCount;
  final int obligationCount;
  final int receivableCount;
  final int monteCarloRuns;
  final int beamWidth;
  final String engineVersion;

  Metadata.fromJson(Map<String, dynamic> json)
      : masterJsonLastUpdated = json['master_json_last_updated'],
        transactionCount = json['transaction_count'],
        obligationCount = json['obligation_count'],
        receivableCount = json['receivable_count'],
        monteCarloRuns = json['monte_carlo_runs'],
        beamWidth = json['beam_width'],
        engineVersion = json['engine_version'];
}
