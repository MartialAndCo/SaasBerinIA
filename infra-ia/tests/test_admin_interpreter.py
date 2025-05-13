"""
Test script for AdminInterpreterAgent to verify it correctly handles
non-existent agent requests.
"""

import sys
import os
import json
import logging

# Add the parent directory to the path so we can import the agent
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test-admin-interpreter")

# Import the agent
from agents.admin_interpreter.admin_interpreter_agent import AdminInterpreterAgent

def test_valid_agent_request():
    """Test with a valid agent name"""
    logger.info("Testing with valid agent name (ScraperAgent)...")
    
    interpreter = AdminInterpreterAgent()
    
    # Modify system prompt path to use absolute path
    interpreter.prompt_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                          "agents/admin_interpreter/prompt.txt")
    
    # Analyze the message directly without executing the agent
    analysis = interpreter._analyze_admin_message("Demande au ScraperAgent de récupérer 50 leads dans la niche coaching")
    
    logger.info(f"Analysis result: {json.dumps(analysis, indent=2, ensure_ascii=False)}")
    
    # Verify the analysis contains a valid agent name - handle different response formats
    if "action" in analysis and "target_agent" in analysis["action"]:
        assert analysis["action"]["target_agent"] in interpreter.VALID_AGENTS
    elif "to" in analysis:  # Alternative format returned by LLM
        # Map the 'to' field to expected format for testing
        analysis["action"] = {"target_agent": analysis["to"]}
        assert analysis["to"] in interpreter.VALID_AGENTS
    
    logger.info(f"Valid agent name detected: {analysis['action']['target_agent']}")
    return analysis

def test_invalid_agent_request():
    """Test with an invalid agent name"""
    logger.info("Testing with invalid agent name (LeadsAgent)...")
    
    interpreter = AdminInterpreterAgent()
    
    # Modify system prompt path to use absolute path
    interpreter.prompt_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                          "agents/admin_interpreter/prompt.txt")
    
    # Analyze the message directly
    analysis = interpreter._analyze_admin_message("Combien de leads ont été contactés par le LeadsAgent ?")
    
    logger.info(f"Analysis result: {json.dumps(analysis, indent=2, ensure_ascii=False)}")
    
    # Check if the response properly handles the non-existent agent
    assert "action" in analysis
    assert "target_agent" in analysis["action"]
    
    # The target agent should be in the valid agents list
    assert analysis["action"]["target_agent"] in interpreter.VALID_AGENTS
    
    # Check if the original agent was recorded
    if "original_target" in analysis["action"]:
        logger.info(f"Successfully mapped invalid agent '{analysis['action']['original_target']}' to '{analysis['action']['target_agent']}'")
    
    return analysis

def test_nonspecific_request():
    """Test with a request that doesn't specifically name an agent"""
    logger.info("Testing with non-specific request (about leads)...")
    
    interpreter = AdminInterpreterAgent()
    
    # Modify system prompt path to use absolute path
    interpreter.prompt_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                          "agents/admin_interpreter/prompt.txt")
    
    # Analyze the message directly
    analysis = interpreter._analyze_admin_message("Combien de leads ont été contactés aujourd'hui?")
    
    logger.info(f"Analysis result: {json.dumps(analysis, indent=2, ensure_ascii=False)}")
    
    # Check if it routes to an appropriate agent for this kind of request
    assert "action" in analysis
    
    if "target_agent" in analysis["action"]:
        agent = analysis["action"]["target_agent"]
        assert agent in interpreter.VALID_AGENTS, f"Agent {agent} is not valid"
        logger.info(f"Request about leads routed to {agent}")
    
    return analysis

def test_completely_unrelated_request():
    """Test with a request that is completely unrelated to any agent capability"""
    logger.info("Testing with completely unrelated request...")
    
    interpreter = AdminInterpreterAgent()
    
    # Modify system prompt path to use absolute path
    interpreter.prompt_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                          "agents/admin_interpreter/prompt.txt")
    
    # Analyze the message directly
    analysis = interpreter._analyze_admin_message("Quelle est la capitale de la France?")
    
    logger.info(f"Analysis result: {json.dumps(analysis, indent=2, ensure_ascii=False)}")
    
    # For unrelated requests, we expect either "unknown" intent or OverseerAgent
    if analysis["intent"] == "unknown":
        logger.info("Unrelated request correctly identified as 'unknown' intent")
    elif "action" in analysis and "target_agent" in analysis["action"]:
        agent = analysis["action"]["target_agent"]
        assert agent in interpreter.VALID_AGENTS, f"Agent {agent} is not valid"
        logger.info(f"Unrelated request routed to {agent} (should ideally be OverseerAgent)")
        assert agent == "OverseerAgent", "Unrelated requests should be routed to OverseerAgent"
    
    return analysis

if __name__ == "__main__":
    print("\n=== TESTING ADMIN INTERPRETER AGENT ===\n")
    
    all_tests_passed = True
    
    try:
        print("\n--- Testing valid agent request ---")
        valid_result = test_valid_agent_request()
        print("✅ Valid agent request test passed")
        
        print("\n--- Testing invalid agent request ---")
        invalid_result = test_invalid_agent_request()
        print("✅ Invalid agent request test passed")
        
        print("\n--- Testing non-specific request ---")
        nonspecific_result = test_nonspecific_request()
        print("✅ Non-specific request test passed")
        
        print("\n--- Testing completely unrelated request ---")
        unrelated_result = test_completely_unrelated_request()
        print("✅ Unrelated request test passed")
        
        print("\n=== ALL TESTS COMPLETED SUCCESSFULLY ===")
        
    except AssertionError as ae:
        all_tests_passed = False
        logger.error(f"Assertion error: {str(ae)}")
        import traceback
        logger.error(traceback.format_exc())
    except Exception as e:
        all_tests_passed = False
        logger.error(f"Test failed with error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    
    if not all_tests_passed:
        sys.exit(1)
