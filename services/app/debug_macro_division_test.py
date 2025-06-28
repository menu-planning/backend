#!/usr/bin/env python3
"""
Simple test to verify macro_division logic with zero values.
"""

def test_macro_division_logic():
    """Test the macro division logic directly."""
    
    test_cases = [
        (0.0, 0.0, 0.0),    # All zero - should return None
        (0.0, 500.0, 0.0),  # Only protein - should work
        (500.0, 0.0, 0.0),  # Only carbs - should work  
        (0.0, 0.0, 200.0),  # Only fat - should work
    ]
    
    for carb, protein, fat in test_cases:
        print(f"\nTesting: carb={carb}, protein={protein}, fat={fat}")
        
        # This is the current logic from macro_division property
        if carb is None or protein is None or fat is None:
            result = None
            reason = "One or more values is None"
        else:
            denominator = carb + protein + fat
            if denominator == 0:
                result = None
                reason = "Total macros is zero"
            else:
                carb_pct = (carb / denominator) * 100
                protein_pct = (protein / denominator) * 100
                fat_pct = (fat / denominator) * 100
                result = {
                    'carbohydrate': carb_pct,
                    'protein': protein_pct, 
                    'fat': fat_pct
                }
                reason = "Success"
        
        print(f"  Result: {result}")
        print(f"  Reason: {reason}")
        
        expected_total = carb + protein + fat
        if expected_total > 0:
            expected = "Should return MacroDivision"
            actual = "Returns MacroDivision" if result is not None else "Returns None"
            status = "✅ PASS" if result is not None else "❌ FAIL"
        else:
            expected = "Should return None"
            actual = "Returns None" if result is None else "Returns MacroDivision"
            status = "✅ PASS" if result is None else "❌ FAIL"
        
        print(f"  Expected: {expected}")
        print(f"  Actual: {actual}")
        print(f"  Status: {status}")

if __name__ == "__main__":
    test_macro_division_logic() 