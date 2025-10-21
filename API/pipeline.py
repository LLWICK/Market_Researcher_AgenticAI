# agents/pipeline.py

from Agent_setup import run_team_b

def run_pipeline(query: str):
    """Orchestrate both Agent Teams."""
    #team_a_output = run_team_a(query)
    team_b_output = run_team_b(query)
    
    return {
        #"team_a": team_a_output,
        "team_b": team_b_output,
    }
