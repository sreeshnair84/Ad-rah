import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:adara_screen_digital_signage/shared/widgets/app_button.dart';

void main() {
  group('AppButton Widget Tests', () {
    testWidgets('should render primary button correctly', (tester) async {
      var pressed = false;
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AppButton(
              text: 'Primary Button',
              onPressed: () => pressed = true,
            ),
          ),
        ),
      );

      expect(find.text('Primary Button'), findsOneWidget);
      expect(find.byType(ElevatedButton), findsOneWidget);
      
      await tester.tap(find.byType(AppButton));
      expect(pressed, true);
    });

    testWidgets('should render secondary button correctly', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AppButton(
              text: 'Secondary Button',
              onPressed: () {},
              variant: AppButtonVariant.secondary,
            ),
          ),
        ),
      );

      expect(find.text('Secondary Button'), findsOneWidget);
      expect(find.byType(OutlinedButton), findsOneWidget);
    });

    testWidgets('should render tertiary button correctly', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AppButton(
              text: 'Tertiary Button',
              onPressed: () {},
              variant: AppButtonVariant.tertiary,
            ),
          ),
        ),
      );

      expect(find.text('Tertiary Button'), findsOneWidget);
      expect(find.byType(TextButton), findsOneWidget);
    });

    testWidgets('should render destructive button correctly', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AppButton(
              text: 'Destructive Button',
              onPressed: () {},
              variant: AppButtonVariant.destructive,
            ),
          ),
        ),
      );

      expect(find.text('Destructive Button'), findsOneWidget);
      expect(find.byType(ElevatedButton), findsOneWidget);
    });

    testWidgets('should show loading state correctly', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AppButton(
              text: 'Loading Button',
              onPressed: () {},
              isLoading: true,
            ),
          ),
        ),
      );

      expect(find.text('Loading...'), findsOneWidget);
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
    });

    testWidgets('should be disabled when isEnabled is false', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AppButton(
              text: 'Disabled Button',
              onPressed: () {},
              isEnabled: false,
            ),
          ),
        ),
      );

      final button = tester.widget<ElevatedButton>(find.byType(ElevatedButton));
      expect(button.onPressed, isNull);
    });

    testWidgets('should be disabled when onPressed is null', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: AppButton(
              text: 'Null Callback Button',
              onPressed: null,
            ),
          ),
        ),
      );

      final button = tester.widget<ElevatedButton>(find.byType(ElevatedButton));
      expect(button.onPressed, isNull);
    });

    testWidgets('should render with icon correctly', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AppButton(
              text: 'Icon Button',
              onPressed: () {},
              icon: Icons.add,
            ),
          ),
        ),
      );

      expect(find.text('Icon Button'), findsOneWidget);
      expect(find.byIcon(Icons.add), findsOneWidget);
    });

    testWidgets('should have correct width when specified', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AppButton(
              text: 'Fixed Width Button',
              onPressed: () {},
              width: 200,
            ),
          ),
        ),
      );

      final sizedBox = tester.widget<SizedBox>(
        find.ancestor(
          of: find.byType(ElevatedButton),
          matching: find.byType(SizedBox),
        ).first,
      );
      expect(sizedBox.width, 200);
    });

    testWidgets('should apply different sizes correctly', (tester) async {
      // Test small size
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AppButton(
              text: 'Small Button',
              onPressed: () {},
              size: AppButtonSize.small,
            ),
          ),
        ),
      );

      final smallButton = tester.widget<ElevatedButton>(find.byType(ElevatedButton));
      final smallStyle = smallButton.style!;
      
      // Test large size
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AppButton(
              text: 'Large Button',
              onPressed: () {},
              size: AppButtonSize.large,
            ),
          ),
        ),
      );

      final largeButton = tester.widget<ElevatedButton>(find.byType(ElevatedButton));
      final largeStyle = largeButton.style!;
      
      // Small and large buttons should have different padding
      expect(smallStyle, isNot(equals(largeStyle)));
    });
  });

  group('AppIconButton Widget Tests', () {
    testWidgets('should render icon button correctly', (tester) async {
      var pressed = false;
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AppIconButton(
              icon: Icons.settings,
              onPressed: () => pressed = true,
              tooltip: 'Settings',
            ),
          ),
        ),
      );

      expect(find.byIcon(Icons.settings), findsOneWidget);
      expect(find.byType(IconButton), findsOneWidget);
      
      await tester.tap(find.byType(AppIconButton));
      expect(pressed, true);
    });

    testWidgets('should show tooltip on long press', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AppIconButton(
              icon: Icons.help,
              onPressed: () {},
              tooltip: 'Help',
            ),
          ),
        ),
      );

      await tester.longPress(find.byType(AppIconButton));
      await tester.pumpAndSettle();

      expect(find.text('Help'), findsOneWidget);
    });

    testWidgets('should be disabled when isEnabled is false', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AppIconButton(
              icon: Icons.delete,
              onPressed: () {},
              isEnabled: false,
            ),
          ),
        ),
      );

      final button = tester.widget<IconButton>(find.byType(IconButton));
      expect(button.onPressed, isNull);
    });

    testWidgets('should apply different sizes correctly', (tester) async {
      // Test small size
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AppIconButton(
              icon: Icons.add,
              onPressed: () {},
              size: AppButtonSize.small,
            ),
          ),
        ),
      );

      // Check if small icon is rendered
      expect(find.byIcon(Icons.add), findsOneWidget);
      
      // Test large size
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AppIconButton(
              icon: Icons.add,
              onPressed: () {},
              size: AppButtonSize.large,
            ),
          ),
        ),
      );

      // Check if large icon is rendered
      expect(find.byIcon(Icons.add), findsOneWidget);
    });

    testWidgets('should apply different variants correctly', (tester) async {
      // Test primary variant
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AppIconButton(
              icon: Icons.star,
              onPressed: () {},
              variant: AppButtonVariant.primary,
            ),
          ),
        ),
      );

      expect(find.byIcon(Icons.star), findsOneWidget);
      
      // Test destructive variant
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AppIconButton(
              icon: Icons.delete,
              onPressed: () {},
              variant: AppButtonVariant.destructive,
            ),
          ),
        ),
      );

      expect(find.byIcon(Icons.delete), findsOneWidget);
    });
  });
}