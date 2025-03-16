import LM_studio_local as lm

class EmailAgent:
    def __init__(self, role, client):
        self.role = role
        self.client = client

    def process(self, content):
        prompts = {
            # Analyzer prompt - extracts key information from email
            "analyzer": """SYSTEM: You are an expert email analyzer with years of experience in professional communication. Your role is to break down emails into their key components and provide clear, actionable insights.

            As an email analyzer, examine this email content and extract:
            1. Main topics and key points
            2. Urgency level
            3. Required actions
            4. Tone of the message

            INSTRUCTIONS:
            • Focus on extracting factual information without interpretation
            • Identify any deadlines or time-sensitive elements
            • Categorize the email priority (high/medium/low)
            • Show output only - no explanations or additional commentary

            Email: {content}

            Provide a structured analysis.""",
            # Drafter prompt - creates email response based on analysis
            "drafter": """SYSTEM: You are a professional email response specialist with extensive experience in business communication. Your role is to craft clear, effective, and appropriate email responses based on provided analysis.

            As an email response drafter, using this analysis: {content}
            Create a professional email response that:
            1. Addresses all key points
            2. Matches the appropriate tone
            3. Includes clear next steps

            INSTRUCTIONS:
            • Maintain consistent professional tone throughout response
            • Include specific details from the analysis
            • End with clear actionable next steps
            • Show output only - provide just the email response

            Write the complete response.""",
            # Reviewer prompt - evaluates the draft response
            "reviewer": """SYSTEM: You are a senior email quality assurance specialist with a keen eye for detail and professional standards. Your role is to ensure all email responses meet the highest standards of business communication.

            As an email quality reviewer, evaluate this draft response: {content}
            Check for:
            1. Professionalism and appropriateness
            2. Completeness (all points addressed)
            3. Clarity and tone
            4. Potential improvements

            INSTRUCTIONS:
            • Verify all original questions/requests are addressed
            • Check for appropriate formality and politeness
            • Ensure response is concise and well-structured
            • Show output only - return APPROVED or NEEDS_REVISION with brief feedback

            Return either APPROVED or NEEDS_REVISION with specific feedback.""",
        }

        return lm.prompt_llm(prompts[self.role].format(content=content))


if __name__ == "__main__":
    print("\n\nWelcome to the Email Processing System!\n")
    # Example usage with email content
    sample_emails = [
        """Subject: Project Update Request
        Hi team, I hope this email finds you well. Could you please provide an update
        on the current status of the ML project? We need to know the timeline for
        the next deliverable. Thanks!""",
        """Subject: Meeting Scheduling
        Hello, I'd like to schedule a meeting to discuss the recent developments.
        Would tomorrow at 2 PM work for you? Best regards.""",
    ]

    # Process the sample emails
    analyzer = EmailAgent("analyzer", lm.client)
    drafter = EmailAgent("drafter", lm.client)
    reviewer = EmailAgent("reviewer", lm.client)

    for i, email_content in enumerate(sample_emails):
        print(f"\nProcessing email {i+1}")

        # Step 1: Analyze email
        print("\nAnalyzing email content...")
        analysis = analyzer.process(email_content)

        # Step 2: Draft response
        print("\nDrafting response based on analysis...")
        draft = drafter.process(analysis)

        # Display formatted output
        print("\n" + "=" * 50)
        print("ORIGINAL EMAIL:\n")
        print(email_content)
        print("\n" + "=" * 50)
        print("DRAFT RESPONSE:\n")
        print(draft)
        print("\n" + "=" * 50)
        # input("Press Enter to continue...")
