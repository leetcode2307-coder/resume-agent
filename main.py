# main.py
import streamlit as st
from app.graph.workflow import workflow_result
from app.llm import fallback_llm
from mdclense.parser import MarkdownParser
import json
import time

# Page configuration
st.set_page_config(
    page_title="Resume Analyzer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f1f1f;
        margin-bottom: 1rem;
    }
    .score-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .score-card h2 {
        margin: 0;
        font-size: 2.5rem;
    }
    .score-card p {
        margin: 0;
        opacity: 0.9;
    }
    .section-header {
        font-size: 1.2rem;
        font-weight: 600;
        margin-top: 1.5rem;
        margin-bottom: 0.5rem;
        color: #2c3e50;
    }
    .skill-tag {
        display: inline-block;
        background: #e8f0fe;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        margin: 0.25rem;
        font-size: 0.9rem;
    }
    .skill-tag.matching {
        background: #d4edda;
        color: #155724;
    }
    .skill-tag.missing {
        background: #f8d7da;
        color: #721c24;
    }
    .skill-tag.nice-to-have {
        background: #fff3cd;
        color: #856404;
    }
    .stExpander {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        margin-bottom: 0.5rem;
    }
    .input-section {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
    }
    </style>
""", unsafe_allow_html=True)

def display_metrics(workflow_data):
    """Display key metrics in a row"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
            <div class="score-card">
                <p>Match Score</p>
                <h2>{workflow_data.get('initial_match_score', 0)}%</h2>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div class="score-card">
                <p>ATS Score</p>
                <h2>{workflow_data.get('ats_score', 0)}%</h2>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        critic_score = workflow_data.get('critic_score', 'N/A')
        st.markdown(f"""
            <div class="score-card">
                <p>Critic Score</p>
                <h2>{critic_score}/10</h2>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        iterations = workflow_data.get('rewrite_iteration', 0)
        st.markdown(f"""
            <div class="score-card">
                <p>Rewrites</p>
                <h2>{iterations}</h2>
            </div>
        """, unsafe_allow_html=True)

def display_skills(workflow_data):
    """Display skills with color coding"""
    st.markdown('<div class="section-header">🎯 Skills Analysis</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**✅ Matching Skills**")
        matching = workflow_data.get('matching_skills', [])
        if matching:
            for skill in matching:
                st.markdown(f'<span class="skill-tag matching">{skill}</span>', unsafe_allow_html=True)
        else:
            st.caption("No matching skills found")
        
        st.markdown("**⭐ Nice-to-Have Skills**")
        nice_to_have = workflow_data.get('nice_to_have_skills', [])
        if nice_to_have:
            for skill in nice_to_have:
                st.markdown(f'<span class="skill-tag nice-to-have">{skill}</span>', unsafe_allow_html=True)
        else:
            st.caption("No nice-to-have skills listed")
    
    with col2:
        st.markdown("**❌ Missing Skills**")
        missing = workflow_data.get('missing_skills', [])
        if missing:
            for skill in missing:
                st.markdown(f'<span class="skill-tag missing">{skill}</span>', unsafe_allow_html=True)
        else:
            st.caption("No missing skills identified")

def display_strengths_weaknesses(workflow_data):
    """Display strengths and weaknesses"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="section-header">💪 Strengths</div>', unsafe_allow_html=True)
        strengths = workflow_data.get('strengths', [])
        if strengths:
            for s in strengths:
                st.markdown(f"• {s}")
        else:
            st.caption("No strengths listed")
    
    with col2:
        st.markdown('<div class="section-header">⚠️ Areas for Improvement</div>', unsafe_allow_html=True)
        weaknesses = workflow_data.get('weaknesses', [])
        if weaknesses:
            for w in weaknesses:
                st.markdown(f"• {w}")
        else:
            st.caption("No weaknesses identified")

def display_interview_prep(workflow_data):
    """Display interview preparation content"""
    st.markdown('<div class="section-header">🎤 Interview Preparation</div>', unsafe_allow_html=True)
    
    tabs = st.tabs(["📋 Questions", "💡 Tips", "📚 Topics"])
    
    with tabs[0]:
        questions = workflow_data.get('interview_questions', [])
        if questions:
            for i, q in enumerate(questions, 1):
                st.markdown(f"**{i}.** {q}")
        else:
            st.info("No interview questions generated")
        
        # Technical and gap questions
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Technical Questions**")
            tech_qs = workflow_data.get('technical_questions', [])
            if tech_qs:
                for q in tech_qs:
                    st.markdown(f"• {q}")
            else:
                st.caption("None")
        
        with col2:
            st.markdown("**Gap Questions**")
            gap_qs = workflow_data.get('gap_questions', [])
            if gap_qs:
                for q in gap_qs:
                    st.markdown(f"• {q}")
            else:
                st.caption("None")
    
    with tabs[1]:
        tips = workflow_data.get('preparation_tips', [])
        if tips:
            for tip in tips:
                st.markdown(f"💡 {tip}")
        else:
            st.info("No preparation tips available")
    
    with tabs[2]:
        topics = workflow_data.get('key_topics_to_review', [])
        if topics:
            for topic in topics:
                st.markdown(f"📖 {topic}")
        else:
            st.info("No key topics identified")

def display_resume_content(workflow_data):
    """Display rewritten resume and cover letter"""
    st.markdown('<div class="section-header">📝 Resume & Cover Letter</div>', unsafe_allow_html=True)
    
    tabs = st.tabs(["📄 Rewritten Resume", "📎 Cover Letter", "✏️ Bullet Points"])
    
    with tabs[0]:
        resume = workflow_data.get('rewritten_resume', '')
        if resume and resume != 'Not rewritten':
            with st.expander("View Rewritten Resume", expanded=True):
                st.markdown(resume)
        else:
            st.info("Resume not rewritten")
    
    with tabs[1]:
        cover_letter = workflow_data.get('cover_letter', '')
        if cover_letter and cover_letter != 'Not generated':
            with st.expander("View Cover Letter", expanded=True):
                st.markdown(cover_letter)
        else:
            st.info("Cover letter not generated")
    
    with tabs[2]:
        bullet_points = workflow_data.get('rewritten_bullet_points', [])
        if bullet_points:
            for bp in bullet_points:
                st.markdown(f"• {bp}")
        else:
            st.info("No rewritten bullet points")

def display_critic_feedback(workflow_data):
    """Display critic feedback"""
    st.markdown('<div class="section-header">📊 Detailed Feedback</div>', unsafe_allow_html=True)
    
    feedback = workflow_data.get('critic_feedback', [])
    errors = workflow_data.get('detected_errors', [])
    weak_phrasing = workflow_data.get('weak_phrasing', [])
    
    if feedback or errors or weak_phrasing:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**📝 Feedback**")
            if feedback:
                for f in feedback:
                    st.markdown(f"• {f}")
            else:
                st.caption("No feedback")
        
        with col2:
            st.markdown("**⚠️ Detected Errors**")
            if errors:
                for e in errors:
                    st.markdown(f"• {e}")
            else:
                st.caption("No errors detected")
        
        with col3:
            st.markdown("**💬 Weak Phrasing**")
            if weak_phrasing:
                for w in weak_phrasing:
                    st.markdown(f"• {w}")
            else:
                st.caption("No weak phrasing identified")
    else:
        st.info("No critic feedback available")

def main():
    st.markdown('<div class="main-header">📄 Resume Analyzer</div>', unsafe_allow_html=True)
    st.caption("Comprehensive resume analysis with ATS scoring, skill matching, and interview preparation")
    
    # Input section
    st.markdown('<div class="input-section">', unsafe_allow_html=True)
    st.subheader("📝 Input Your Documents")
    
    col1, col2 = st.columns(2)
    
    with col1:
        resume_text = st.text_area(
            "📄 Resume Text",
            height=300,
            placeholder="Paste your resume text here...",
            help="Enter your resume content in plain text format"
        )
        
        # Optional file upload for resume
        uploaded_resume = st.file_uploader(
            "Or upload resume file",
            type=['txt', 'md', 'pdf'],
            help="Upload a text file containing your resume"
        )
        if uploaded_resume:
            try:
                resume_text = uploaded_resume.read().decode('utf-8')
                st.success("✅ Resume uploaded successfully!")
            except Exception as e:
                st.error(f"Error reading file: {e}")
    
    with col2:
        job_description = st.text_area(
            "💼 Job Description",
            height=300,
            placeholder="Paste the job description here...",
            help="Enter the job description in plain text format"
        )
        
        # Optional file upload for job description
        uploaded_job = st.file_uploader(
            "Or upload job description file",
            type=['txt', 'md', 'pdf'],
            help="Upload a text file containing the job description"
        )
        if uploaded_job:
            try:
                job_description = uploaded_job.read().decode('utf-8')
                st.success("✅ Job description uploaded successfully!")
            except Exception as e:
                st.error(f"Error reading file: {e}")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Analysis button - disabled if inputs are empty
    analyze_button = st.button(
        "🚀 Analyze Resume", 
        type="primary", 
        use_container_width=True,
        disabled=not (resume_text and job_description)
    )
    
    if analyze_button:
        with st.spinner("Analyzing your resume..."):
            try:
                # Execute the workflow with the provided inputs
                workflow_data = workflow_result(resume_text, job_description)
                
                if workflow_data:
                    # Store in session state to persist results
                    st.session_state['workflow_data'] = workflow_data
                    st.session_state['analyzed'] = True
                    
                    # Display metrics
                    display_metrics(workflow_data)
                    st.divider()
                    
                    # Display skills
                    display_skills(workflow_data)
                    st.divider()
                    
                    # Display strengths and weaknesses
                    display_strengths_weaknesses(workflow_data)
                    st.divider()
                    
                    # Display interview prep
                    display_interview_prep(workflow_data)
                    st.divider()
                    
                    # Display resume content
                    display_resume_content(workflow_data)
                    st.divider()
                    
                    # Display critic feedback
                    display_critic_feedback(workflow_data)
                    
                    # Export option
                    st.divider()
                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            label="📥 Export Results (JSON)",
                            data=json.dumps(workflow_data, indent=2),
                            file_name="resume_analysis_results.json",
                            mime="application/json",
                            use_container_width=True
                        )
                    with col2:
                        # Generate a summary report
                        summary = f"""
                        Resume Analysis Summary
                        ========================
                        Role: {workflow_data.get('role', 'N/A')}
                        Company: {workflow_data.get('company', 'N/A')}
                        Seniority: {workflow_data.get('seniority', 'N/A')}
                        
                        Scores:
                        - Match Score: {workflow_data.get('initial_match_score', 0)}%
                        - ATS Score: {workflow_data.get('ats_score', 0)}%
                        - Critic Score: {workflow_data.get('critic_score', 'N/A')}/10
                        
                        Skills Summary:
                        - Matching: {len(workflow_data.get('matching_skills', []))} skills
                        - Missing: {len(workflow_data.get('missing_skills', []))} skills
                        - Nice-to-Have: {len(workflow_data.get('nice_to_have_skills', []))} skills
                        
                        Interview Prep:
                        - Questions: {len(workflow_data.get('interview_questions', []))} generated
                        - Tips: {len(workflow_data.get('preparation_tips', []))} provided
                        """
                        st.download_button(
                            label="📋 Download Summary",
                            data=summary,
                            file_name="resume_analysis_summary.txt",
                            mime="text/plain",
                            use_container_width=True
                        )
                else:
                    st.error("No data returned from analysis")
                    st.session_state['analyzed'] = False
            
            except Exception as e:
                st.error(f"Analysis failed: {str(e)}")
                st.exception(e)
                st.session_state['analyzed'] = False
    
    # Display instructions when no analysis has been performed
    if not st.session_state.get('analyzed', False) and not analyze_button:
        st.info("👆 Enter your resume and job description above, then click 'Analyze Resume' to get detailed feedback.")
        
        # Show what the analysis includes
        with st.expander("ℹ️ What this analysis includes"):
            st.markdown("""
            - **Match Score**: How well your resume matches the job description
            - **ATS Score**: Resume compatibility with Applicant Tracking Systems
            - **Skills Analysis**: Matching, missing, and nice-to-have skills
            - **Strengths & Weaknesses**: Key areas of your resume
            - **Interview Preparation**: Questions, tips, and topics to review
            - **Resume Enhancement**: Rewritten content and bullet points
            - **Detailed Feedback**: Critic score with actionable insights
            """)
        
        # Tips for best results
        with st.expander("💡 Tips for best results"):
            st.markdown("""
            **Resume Tips:**
            - Include clear work experience with bullet points
            - List technical skills and certifications
            - Use action verbs and quantify achievements
            
            **Job Description Tips:**
            - Include the complete job description
            - Highlight required skills and qualifications
            - Include company culture and values if mentioned
            
            **Format:** Plain text works best for accurate analysis.
            """)

if __name__ == "__main__":
    main()