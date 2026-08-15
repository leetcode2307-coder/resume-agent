from app.graph.workflow import workflow_result
from app.llm import fallback_llm
from mdclense.parser import MarkdownParser
import json

def main():
    parser = MarkdownParser()
    
    try:
        # Execute the workflow to get the result
        workflow_data = workflow_result()
        
        # Define a system prompt for the fallback LLM
        system_prompt = """
        You are a professional resume and career advisor.
        Return the output in clean, well-structured plain text format.
        Organize the information clearly with sections and bullet points where appropriate.
        """
        
        # Prepare the human message with formatted workflow data
        human_message = f"""
        Please analyze and summarize the following resume analysis data:
        
        === RESUME ANALYSIS RESULTS ===
        Role: {workflow_data.get('role', 'Not specified')}
        Seniority: {workflow_data.get('seniority', 'Not specified')}
        Company: {workflow_data.get('company', 'Not specified')}
        
        Initial Match Score: {workflow_data.get('initial_match_score', 0)}%
        ATS Score: {workflow_data.get('ats_score', 0)}%
        
        Matching Skills: {', '.join(workflow_data.get('matching_skills', []))}
        Missing Skills: {', '.join(workflow_data.get('missing_skills', []))}
        Nice-to-Have Skills: {', '.join(workflow_data.get('nice_to_have_skills', []))}
        
        Strengths: {', '.join(workflow_data.get('strengths', []))}
        Weaknesses: {', '.join(workflow_data.get('weaknesses', []))}
        
        Keyword Matches: {', '.join(workflow_data.get('keyword_matches', []))}
        Keyword Gaps: {', '.join(workflow_data.get('keyword_gaps', []))}
        
        Rewritten Resume: {workflow_data.get('rewritten_resume', 'Not rewritten')}
        Rewritten Bullet Points: 
        {chr(10).join(['- ' + bp for bp in workflow_data.get('rewritten_bullet_points', [])])}
        
        Cover Letter: {workflow_data.get('cover_letter', 'Not generated')}
        
        Critic Score: {workflow_data.get('critic_score', 'Not evaluated')}/10
        Critic Feedback: {', '.join(workflow_data.get('critic_feedback', []))}
        Detected Errors: {', '.join(workflow_data.get('detected_errors', []))}
        Weak Phrasing: {', '.join(workflow_data.get('weak_phrasing', []))}
        
        Interview Questions: {', '.join(workflow_data.get('interview_questions', []))}
        Technical Questions: {', '.join(workflow_data.get('technical_questions', []))}
        Gap Questions: {', '.join(workflow_data.get('gap_questions', []))}
        
        Preparation Tips: {', '.join(workflow_data.get('preparation_tips', []))}
        Key Topics to Review: {', '.join(workflow_data.get('key_topics_to_review', []))}
        Expected Questions: {', '.join(workflow_data.get('expected_questions', []))}
        
        Number of Rewrite Iterations: {workflow_data.get('rewrite_iteration', 0)}
        """
        
        # Try to use the fallback LLM with proper error handling
        result_text = None
        
        try:
            # Check if fallback_llm is an instance with invoke method
            if hasattr(fallback_llm, 'invoke'):
                try:
                    response = fallback_llm.invoke(
                        [
                            ("system", system_prompt),
                            ("human", human_message)
                        ]
                    )
                    result_text = response.content
                except Exception as e:
                    print(f"LLM invocation error: {e}")
                    # Check if response was an error response
                    if hasattr(e, 'response') and hasattr(e.response, 'text'):
                        try:
                            error_data = json.loads(e.response.text)
                            if 'error' in error_data:
                                print(f"API Error: {error_data['error'].get('message', 'Unknown error')}")
                        except:
                            pass
                    result_text = None
            
            # If fallback_llm is a callable function
            elif callable(fallback_llm):
                try:
                    response = fallback_llm(system_prompt, human_message)
                    result_text = response
                except Exception as e:
                    print(f"LLM callable error: {e}")
                    result_text = None
            
            # If no LLM is available or all attempts failed
            if result_text is None:
                print("=" * 60)
                print("INFO: LLM API unavailable. Displaying raw analysis results.")
                print("=" * 60)
                print("\n" + "=" * 60)
                print("RESUME ANALYSIS RESULTS")
                print("=" * 60)
                
                # Display the results in a formatted way
                print(f"\n📋 ROLE: {workflow_data.get('role', 'Not specified')}")
                print(f"🏢 COMPANY: {workflow_data.get('company', 'Not specified')}")
                print(f"📊 SENIORITY: {workflow_data.get('seniority', 'Not specified')}")
                
                print(f"\n📈 INITIAL MATCH SCORE: {workflow_data.get('initial_match_score', 0)}%")
                print(f"📊 ATS SCORE: {workflow_data.get('ats_score', 0)}%")
                
                print(f"\n✅ MATCHING SKILLS: {', '.join(workflow_data.get('matching_skills', [])) or 'None'}")
                print(f"❌ MISSING SKILLS: {', '.join(workflow_data.get('missing_skills', [])) or 'None'}")
                
                print(f"\n💪 STRENGTHS: {', '.join(workflow_data.get('strengths', [])) or 'None'}")
                print(f"⚠️  WEAKNESSES: {', '.join(workflow_data.get('weaknesses', [])) or 'None'}")
                
                print(f"\n🔍 KEYWORD MATCHES: {', '.join(workflow_data.get('keyword_matches', [])) or 'None'}")
                print(f"🔍 KEYWORD GAPS: {', '.join(workflow_data.get('keyword_gaps', [])) or 'None'}")
                
                if workflow_data.get('critic_score') is not None:
                    print(f"\n⭐ CRITIC SCORE: {workflow_data.get('critic_score', 0)}/10")
                    print(f"📝 CRITIC FEEDBACK: {', '.join(workflow_data.get('critic_feedback', [])) or 'None'}")
                
                if workflow_data.get('interview_questions'):
                    print(f"\n❓ INTERVIEW QUESTIONS:")
                    for i, q in enumerate(workflow_data.get('interview_questions', []), 1):
                        print(f"  {i}. {q}")
                
                if workflow_data.get('preparation_tips'):
                    print(f"\n💡 PREPARATION TIPS:")
                    for tip in workflow_data.get('preparation_tips', []):
                        print(f"  • {tip}")
                
                print("\n" + "=" * 60)
                return
        
        except Exception as e:
            print(f"Unexpected error with LLM: {e}")
            result_text = None
        
        # If we have LLM response, process it
        if result_text:
            # Convert markdown to plain text and print
            try:
                result = parser.to_plaintext(result_text)
                print(result)
            except Exception as e:
                print(f"Error parsing markdown: {e}")
                print(result_text)  # Print raw text as fallback
        
    except Exception as e:
        print("=" * 60)
        print("ERROR: The workflow execution failed.")
        print("Please check your configuration and try again.")
        print(f"Error details: {e}")
        print("=" * 60)

if __name__ == "__main__":
    main()