from langgraph_supervisor import create_handoff_tool


transfer_to_cedemo_execution = create_handoff_tool(
    agent_name="cedemo_agent",
    description="Transfer to CEDEMO execution agent."
)
transfer_to_cedemo_validation = create_handoff_tool(
    agent_name="cedemo_validation",
    description="Transfer to CEDEMO validation agent."
)
transfer_to_oamscm_execution = create_handoff_tool(
    agent_name="oamscm_agent",
    description="Transfer to OAMSCM execution agent."
)
transfer_to_oamscm_validation = create_handoff_tool(
    agent_name="oamscm_validation",
    description="Transfer to OAMSCM validation agent."
)

transfer_to_cedemo_plan = create_handoff_tool(
    agent_name="cedemo_plan",
    description="Transfer to CEDEMO plan agent."
)

transfer_to_oamscm_plan = create_handoff_tool(
    agent_name="oamscm_plan",
    description="Transfer to OAMSCM plan agent."
)
