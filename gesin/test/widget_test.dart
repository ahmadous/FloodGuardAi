import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gesin/main.dart';

void main() {
  testWidgets('GesinApp smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(
      const ProviderScope(
        child: GesinApp(),
      ),
    );
    // App loads without crash
    expect(find.byType(MaterialApp), findsOneWidget);
  });
}
