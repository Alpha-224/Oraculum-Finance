import 'package:flutter/material.dart';
import '../widgets/glass_container.dart';

class ManualEntryPage extends StatefulWidget {
  const ManualEntryPage({super.key});

  @override
  State<ManualEntryPage> createState() => _ManualEntryPageState();
}

class _ManualEntryPageState extends State<ManualEntryPage> {
  DateTime selectedDate = DateTime.now();
  String transactionType = 'Expense';
  String recurrence = 'One-Time';

  Future<void> _selectDate(BuildContext context) async {
    final DateTime? picked = await showDatePicker(
      context: context,
      initialDate: selectedDate,
      firstDate: DateTime(2000),
      lastDate: DateTime(2101),
      builder: (context, child) {
        return Theme(
          data: ThemeData.dark().copyWith(
            colorScheme: const ColorScheme.dark(
              primary: Colors.tealAccent,
              onPrimary: Colors.black,
              surface: Color(0xff022b1e),
              onSurface: Colors.white,
            ),
          ),
          child: child!,
        );
      },
    );
    if (picked != null && picked != selectedDate) {
      setState(() { selectedDate = picked; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
        title: const Text('Manual Entry', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, letterSpacing: 1.5)),
        backgroundColor: Colors.transparent,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.white),
      ),
      body: SafeArea(
        child: LayoutBuilder(
          builder: (context, constraints) {
            return SingleChildScrollView(
              padding: const EdgeInsets.all(16.0),
              child: ConstrainedBox(
                constraints: BoxConstraints(minHeight: constraints.maxHeight - 32),
                child: GlassContainer(
                  padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 32),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      // ─── TYPE SELECTOR ───
                      const Text('TRANSACTION TYPE', style: TextStyle(color: Colors.white38, fontSize: 13, letterSpacing: 1.5, fontWeight: FontWeight.w600)),
                      const SizedBox(height: 12),
                      SegmentedButton<String>(
                        segments: const [
                          ButtonSegment(value: 'Income', label: Text('Income', style: TextStyle(color: Colors.white, fontSize: 16))),
                          ButtonSegment(value: 'Expense', label: Text('Expenditure', style: TextStyle(color: Colors.white, fontSize: 16))),
                        ],
                        selected: {transactionType},
                        onSelectionChanged: (s) => setState(() => transactionType = s.first),
                        style: ButtonStyle(
                          backgroundColor: WidgetStateProperty.resolveWith<Color>((states) {
                            if (states.contains(WidgetState.selected)) return Colors.teal.shade700;
                            return Colors.white.withOpacity(0.05);
                          }),
                          minimumSize: WidgetStateProperty.all(const Size(0, 52)),
                        ),
                      ),
                      const SizedBox(height: 28),

                      // ─── AMOUNT ───
                      TextFormField(
                        decoration: const InputDecoration(
                          labelText: 'Amount (₹)',
                          labelStyle: TextStyle(fontSize: 18),
                          icon: Icon(Icons.currency_rupee, color: Colors.tealAccent, size: 28),
                        ),
                        keyboardType: const TextInputType.numberWithOptions(decimal: true),
                        style: const TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 28),

                      // ─── RECURRENCE ───
                      const Text('FREQUENCY', style: TextStyle(color: Colors.white38, fontSize: 13, letterSpacing: 1.5, fontWeight: FontWeight.w600)),
                      const SizedBox(height: 12),
                      SegmentedButton<String>(
                        segments: const [
                          ButtonSegment(value: 'One-Time', label: Text('One-Time', style: TextStyle(color: Colors.white, fontSize: 16))),
                          ButtonSegment(value: 'Recurring', label: Text('Recurring', style: TextStyle(color: Colors.white, fontSize: 16))),
                        ],
                        selected: {recurrence},
                        onSelectionChanged: (s) => setState(() => recurrence = s.first),
                        style: ButtonStyle(
                          backgroundColor: WidgetStateProperty.resolveWith<Color>((states) {
                            if (states.contains(WidgetState.selected)) return Colors.teal.shade700;
                            return Colors.white.withOpacity(0.05);
                          }),
                          minimumSize: WidgetStateProperty.all(const Size(0, 52)),
                        ),
                      ),
                      const SizedBox(height: 28),

                      // ─── DATE ───
                      InkWell(
                        onTap: () => _selectDate(context),
                        child: InputDecorator(
                          decoration: const InputDecoration(
                            labelText: 'Date',
                            labelStyle: TextStyle(fontSize: 18),
                            icon: Icon(Icons.calendar_today, color: Colors.tealAccent, size: 28),
                          ),
                          child: Text(
                            "${selectedDate.toLocal()}".split(' ')[0],
                            style: const TextStyle(color: Colors.white, fontSize: 20),
                          ),
                        ),
                      ),
                      const SizedBox(height: 28),

                      // ─── TO/FROM ───
                      const TextField(
                        decoration: InputDecoration(
                          labelText: 'To / From',
                          labelStyle: TextStyle(fontSize: 18),
                          icon: Icon(Icons.person, color: Colors.tealAccent, size: 28),
                        ),
                        style: TextStyle(color: Colors.white, fontSize: 20),
                      ),
                      const SizedBox(height: 28),

                      // ─── CATEGORY ───
                      const TextField(
                        decoration: InputDecoration(
                          labelText: 'Category',
                          labelStyle: TextStyle(fontSize: 18),
                          icon: Icon(Icons.category, color: Colors.tealAccent, size: 28),
                        ),
                        style: TextStyle(color: Colors.white, fontSize: 20),
                      ),
                      const SizedBox(height: 40),

                      // ─── SUBMIT ───
                      ElevatedButton(
                        onPressed: () {
                          Navigator.pop(context);
                        },
                        style: ElevatedButton.styleFrom(
                          padding: const EdgeInsets.symmetric(vertical: 18),
                        ),
                        child: const Text('SUBMIT', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, letterSpacing: 2)),
                      ),
                    ],
                  ),
                ),
              ),
            );
          },
        ),
      ),
    );
  }
}
