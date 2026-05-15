import 'package:flutter_riverpod/flutter_riverpod.dart';

// Current selected tab index for bottom navigation
final currentTabProvider = StateProvider<int>((ref) => 0);
