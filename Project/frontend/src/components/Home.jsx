import { useEffect } from 'react'
import './Home.css'
import Aurora from './Aurora'

const Home = ({ onNavigate }) => {
  return (
    <div className="home-shell">
      <div className="home-aurora-bg">
        <Aurora
          colorStops={["#4f46e5", "#7e22ce", "#ec4899"]}
          blend={0.6}
          amplitude={1.2}
          speed={0.8}
        />
      </div>
      
      <div className="home-navbar">
        <div className="home-logo">IntelliQuery</div>
        <div className="home-nav-actions">
          <button className="home-btn-outline" onClick={() => onNavigate('login')}>Log In</button>
          <button className="home-btn-primary" onClick={() => onNavigate('signup')}>Sign Up</button>
        </div>
      </div>

      <div className="home-hero">
        <h1 className="home-title">
          Talk to Your Database in <span>Plain English</span>
        </h1>
        <p className="home-subtitle">
          IntelliQuery bridges the gap between natural language and complex database queries. Connect your MongoDB or PostgreSQL database and start asking questions instantly.
        </p>
        
        <div className="home-cta-group">
          <button className="home-btn-primary home-btn-large" onClick={() => onNavigate('signup')}>
            Get Started for Free
          </button>
          <button className="home-btn-secondary home-btn-large" onClick={() => document.getElementById('features').scrollIntoView({ behavior: 'smooth' })}>
            Explore Features
          </button>
        </div>
      </div>

      <div className="home-features" id="features">
        <h2 className="section-title">Why Choose IntelliQuery?</h2>
        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-number">01</div>
            <h3>Natural Language Processing</h3>
            <p>No SQL or NoSQL knowledge required. Just type your question and let our advanced AI translate it into accurate database queries.</p>
          </div>
          <div className="feature-card">
            <div className="feature-number">02</div>
            <h3>Multi-Database Support</h3>
            <p>Seamlessly connect with MongoDB, PostgreSQL, and other popular databases. Switch between workspaces with a single click.</p>
          </div>
          <div className="feature-card">
            <div className="feature-number">03</div>
            <h3>Claude MCP Integration</h3>
            <p>Connect your database directly to Claude Desktop using our built-in Model Context Protocol server. Chat with your data right from Claude.</p>
          </div>
          <div className="feature-card">
            <div className="feature-number">04</div>
            <h3>Secure & Private</h3>
            <p>Your credentials are encrypted. We ensure safe query execution with built-in intent confirmation to prevent unwanted modifications.</p>
          </div>
        </div>
      </div>

      <div className="home-usecases">
        <h2 className="section-title">Who is IntelliQuery for?</h2>
        <div className="usecases-container">
          <div className="usecase-card">
            <h3>For Data Analysts</h3>
            <p>Skip the boilerplate SQL writing. Instantly explore datasets, test hypotheses, and generate reports at the speed of thought. Focus on insights, not syntax.</p>
          </div>
          <div className="usecase-card">
            <h3>For Product Managers</h3>
            <p>Answer your own product questions without waiting for the data team. Easily query user behavior, adoption metrics, and funnel data directly.</p>
          </div>
          <div className="usecase-card">
            <h3>For Developers</h3>
            <p>Quickly debug production data, verify schema migrations, and inspect state without having to open heavy database GUI clients or CLI tools.</p>
          </div>
        </div>
      </div>

      <div className="home-roles">
        <div className="roles-header">
          <h2 className="section-title">Enterprise-Grade Control</h2>
          <p className="roles-subtitle">Manage workspaces and control access with precision, ensuring security without sacrificing speed.</p>
        </div>
        <div className="roles-grid">
          <div className="role-minimal-card">
            <div className="role-minimal-number">01</div>
            <h4>Workspace Management</h4>
            <p>Create isolated workspaces for different databases, projects, or teams. Seamlessly toggle between them with a single click while maintaining strict data boundaries.</p>
          </div>
          <div className="role-minimal-card">
            <div className="role-minimal-number">02</div>
            <h4>Admin Privileges</h4>
            <p>Maintain total control over the environment. Connect credentials securely, dictate schema visibility, invite team members, and audit cross-workspace query logs.</p>
          </div>
          <div className="role-minimal-card">
            <div className="role-minimal-number">03</div>
            <h4>User Access</h4>
            <p>Provide your team with safe, sandboxed execution. Users enjoy read-only access with interactive intent confirmation, preventing any accidental production changes.</p>
          </div>
        </div>
      </div>

      <footer className="home-footer">
        <div className="footer-content">
          <div className="footer-logo">IntelliQuery</div>
          <p>© 2026 IntelliQuery. All rights reserved.</p>
        </div>
      </footer>
    </div>
  )
}

export default Home
