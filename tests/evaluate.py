import pandas as pd
from src.decision import generate_decision

def evaluate_system(csv_path: str):
    df = pd.read_csv(csv_path)
    total_cases = len(df)
    correct = 0
    incorrect = 0
    
    print(f"Starting evaluation of {total_cases} test cases...")
    
    for index, row in df.iterrows():
        # Construct a rich message containing all order context
        message = (
            f"Message: {row['message']}\n"
            f"Order Value (INR): {row['order_value_inr']}\n"
            f"Days since delivery: {row['days_since_delivery']}\n"
            f"Product Type: {row['product_type']}\n"
            f"Opened Status: {row['opened_status']}\n"
            f"Issue Type: {row['issue_type']}"
        )
        
        expected_action = row['resolved_action']
        
        # Call our decision logic directly
        decision = generate_decision(message)
        predicted_action = decision.get("action", "")
        
        if predicted_action == expected_action:
            correct += 1
            print(f"Case {index+1}: Correct ({predicted_action})")
        else:
            incorrect += 1
            print(f"Case {index+1}: Incorrect. Expected '{expected_action}', got '{predicted_action}'. Reason: {decision.get('reason')}")
            
    accuracy = (correct / total_cases) * 100
    
    print("\n--- Evaluation Results ---")
    print(f"{total_cases} test cases")
    print(f"Correct: {correct}")
    print(f"Incorrect: {incorrect}")
    print(f"Accuracy: {accuracy:.0f}%")

if __name__ == "__main__":
    evaluate_system("data/data/tickets.csv")
