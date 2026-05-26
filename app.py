def show_login():

    import streamlit as st

    st.markdown(
        """
<style>

.stApp{
background:
radial-gradient(
circle at top left,
rgba(255,80,180,.08),
transparent 35%
),

radial-gradient(
circle at bottom right,
rgba(160,0,255,.08),
transparent 40%
),

linear-gradient(
135deg,
#1b1028,
#24133a,
#1c1630
);

color:white;
}

.block-container{
padding-top:2rem;
padding-left:4rem;
padding-right:4rem;
}

.hero-box{
padding-top:60px;
padding-right:50px;
}

.hero-title{
font-size:80px;
font-weight:800;
line-height:0.95;
margin-bottom:20px;
}

.hero-highlight{
color:#ff69c7;
}

.hero-text{
font-size:24px;
color:#a894b7;
max-width:520px;
line-height:1.6;
margin-bottom:70px;
}

.metric-row{
display:flex;
gap:60px;
margin-top:40px;
}

.metric h1{
font-size:56px;
margin:0;
}

.metric p{
margin:0;
color:#8f789a;
}

.ai{
color:#ff69c7;
}

.auto{
color:#38e0aa;
}

.live{
color:#bf82ff;
}

.login-card{

background:
rgba(
40,
20,
55,
0.45
);

backdrop-filter:blur(18px);

padding:50px;

border-radius:28px;

border:
1px solid rgba(
255,
255,
255,
0.08
);

max-width:650px;

margin:auto;

}

.login-title{
font-size:64px;
font-weight:800;
margin-bottom:0;
}

.login-sub{
color:#9a87a8;
margin-bottom:35px;
font-size:22px;
}

.stTextInput input{

background:#2c2d35 !important;

border:none !important;

border-radius:12px !important;

padding:16px !important;

}

.stButton button{

background:
linear-gradient(
135deg,
#ff69c7,
#b86cff
);

color:white;

font-weight:700;

border:none;

border-radius:14px;

padding:12px;

width:100%;

}

</style>
""",
        unsafe_allow_html=True,
    )

    left, right = st.columns([1, 1], gap="large")

    with left:

        st.markdown(
            """
<div class="hero-box">

<div style="font-size:28px;font-weight:700;">
✦ Job Tracker
</div>

<br>

<div class="hero-title">
Land Your
<br>
<span class="hero-highlight">
Dream Job
</span>
</div>

<div class="hero-text">
Track applications,
scan resumes,
match jobs with AI,
and organize everything
in one place.
</div>

<div class="metric-row">

<div class="metric">
<h1 class="ai">AI</h1>
<p>Match Scoring</p>
</div>

<div class="metric">
<h1 class="auto">Auto</h1>
<p>Job Scraping</p>
</div>

<div class="metric">
<h1 class="live">Live</h1>
<p>Status Tracking</p>
</div>

</div>

</div>
""",
            unsafe_allow_html=True,
        )

    with right:

        st.markdown(
            """
<div class="login-card">

<div class="login-title">
Welcome Back
</div>

<div class="login-sub">
Sign in to continue your journey
</div>

</div>
""",
            unsafe_allow_html=True,
        )

        username = st.text_input(
            "Username",
            placeholder="Enter your username"
        )

        password = st.text_input(
            "Password",
            placeholder="Enter your password",
            type="password"
        )

        remember = st.checkbox(
            "Remember me"
        )

        login = st.button(
            "Sign In",
            use_container_width=True
        )

        st.markdown(
            """
<center>

Forgot password?

<br><br>

Don't have an account?
<b style="color:#ff69c7;">
Sign Up
</b>

</center>
""",
            unsafe_allow_html=True
        )

        return login, username, password
