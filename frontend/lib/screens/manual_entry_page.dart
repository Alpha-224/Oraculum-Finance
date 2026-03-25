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
      setState(() {
        selectedDate = picked;
      });
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
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16.0),
          child: GlassContainer(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Income or Expenditure Choice
                SegmentedButton<String>(
                  segments: const [
                    ButtonSegment(value: 'Income', label: Text('Income', style: TextStyle(color: Colors.white))),
                    ButtonSegment(value: 'Expense', label: Text('Expenditure', style: TextStyle(color: Colors.white))),
                  ],
                  selected: {transactionType},
                  onSelectionChanged: (Set<String> newSelection) {
                    setState(() {
                      transactionType = newSelection.first;
                    });
                  },
                  style: ButtonStyle(
                    backgroundColor: MaterialStateProperty.resolveWith<Color>((states) {
                      if (states.contains(MaterialState.selected)) {
                        return Colors.teal.shade700;
                      }
                      return Colors.white.withOpacity(0.05);
                    }),
                  ),
                ),
                const SizedBox(height: 20),
                
                // Amount
                TextFormField(
                  decoration: const InputDecoration(
                    labelText: 'Amount (₹)',
                    icon: Icon(Icons.currency_rupee, color: Colors.tealAccent),
                  ),
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  style: const TextStyle(color: Colors.white, fontSize: 18),
                ),
                const SizedBox(height: 20),

                // Recurring or One-Time Choice
                SegmentedButton<String>(
                  segments: const [
                    ButtonSegment(value: 'One-Time', label: Text('One-Time', style: TextStyle(color: Colors.white))),
                    ButtonSegment(value: 'Recurring', label: Text('Recurring', style: TextStyle(color: Colors.white))),
                  ],
                  selected: {recurrence},
                  onSelectionChanged: (Set<String> newSelection) {
                    setState(() {
                      recurrence = newSelection.first;
                    });
                  },
                  style: ButtonStyle(
                    backgroundColor: MaterialStateProperty.resolveWith<Color>((states) {
                      if (states.contains(MaterialState.selected)) {
                        return Colors.teal.shade700;
                      }
                      return Colors.white.withOpacity(0.05);
                    }),
                  ),
                ),
                const SizedBox(height: 20),

                // Date Picker
                InkWell(
                  onTap: () => _selectDate(context),
                  child: InputDecorator(
                    decoration: const InputDecoration(
                      labelText: 'Date',
                      icon: Icon(Icons.calendar_today, color: Colors.tealAccent),
                    ),
                    child: Text(
                      "${selectedDate.toLocal()}".split(' ')[0],
                      style: const TextStyle(color: Colors.white, fontSize: 16),
                    ),
                  ),
                ),
                const SizedBox(height: 20),

                // To/From Text Box
                const TextField(
                  decoration: InputDecoration(
                    labelText: 'To / From',
                    icon: Icon(Icons.person, color: Colors.tealAccent),
                  ),
                  style: TextStyle(color: Colors.white),
                ),
                const SizedBox(height: 20),

                // Category
                const TextField(
                  decoration: InputDecoration(
                    labelText: 'Category',
                    icon: Icon(Icons.category, color: Colors.tealAccent),
                  ),
                  style: TextStyle(color: Colors.white),
                ),
                const SizedBox(height: 40),

                // Submit
                ElevatedButton(
                  onPressed: () {
                    // Placeholder for Submit Actions
                    Navigator.pop(context);
                  },
                  child: const Text('SUBMIT', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, letterSpacing: 2)),
                )
              ],
            ),
          ),
        ),
      ),
    );
  }
}
