import json
import os
import smtplib
import requests
from email.mime.text import MIMEText
from flask import Flask, render_template_string, request, redirect, url_for, jsonify, send_from_directory

app = Flask(__name__)

# --- CONFIGURATION ---
REVIEWS_FILE = 'reviews.json'
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "1234") 

# EMAIL SETTINGS (Recommendation: Use Environment Variables for production)
SENDER_EMAIL = "stopsquirrelclimb@gmail.com"
SENDER_PASSWORD = "fmlr wqvz sfsu ivls" 
RECEIVER_EMAIL = "stopsquirrelclimb@gmail.com"

# --- DATA HELPERS ---
def get_city_from_ip(ip):
    """Looks up the city based on IP address using ip-api.com."""
    try:
        # Handle proxy headers if hosted on platforms like Heroku
        if ip and ',' in ip:
            ip = ip.split(',')[0].strip()
            
        if ip in ['127.0.0.1', 'localhost'] or ip.startswith('192.168.'):
            return "Berkeley"
        
        response = requests.get(f'http://ip-api.com/json/{ip}?fields=status,city', timeout=5)
        data = response.json()
        if data.get('status') == 'success':
            return data.get('city', 'Berkeley')
        return "Berkeley"
    except Exception as e:
        print(f"City lookup error: {e}")
        return "Berkeley"

def load_reviews():
    if os.path.exists(REVIEWS_FILE):
        with open(REVIEWS_FILE, 'r') as f:
            try: return json.load(f)
            except: return []
    return [] 

def save_all_reviews(reviews):
    with open(REVIEWS_FILE, 'w') as f:
        json.dump(reviews, f)

# --- ROUTES ---
@app.route('/favicon.ico')
@app.route('/favicon.png')
@app.route('/favicon.jpg')
def favicon():
    filename = 'favicon.png' if 'png' in request.path else 'favicon.jpg'
    mimetype = 'image/png' if 'png' in request.path else 'image/jpeg'
    return send_from_directory(os.path.join(app.root_path, 'static'), filename, mimetype=mimetype)

@app.route("/send-support", methods=["POST"])
def send_support():
    data = request.json
    question = data.get("question")
    user_email = data.get("user_email")
    
    subject = f"Support Request from {user_email}"
    body = f"User Email: {user_email}\n\nQuestion:\n{question}"
    
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg['Reply-To'] = user_email 

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Error sending email: {e}")
        return jsonify({"status": "error"}), 500

# --- INSTRUCTIONS DATABASE ---
INSTRUCTION_STEPS = [
    {
        "img": "list.jpg", 
        "caption": "Note: The metal sheet is not shown in this image but is included in your set.",
        "text": """This system stops squirrels from climbing tree trunks, protecting your fruit and bird feeders.
        <ul>
            <b>Parts included:</b>
            <br><br>
            <li><strong>6 plates</strong></li>
            <li><strong>2 plates with hooks</strong></li>
            <li><strong>16 bolts</strong></li>
            <li><strong>16 nuts</strong></li>
            <li><strong>32 washers</strong></li>
            <li><strong>1 wrap-around metal sheet</strong></li>
            <li><strong>1 roll of packing tape</strong></li>
        </ul>"""
    },
    {
            "header": "1. Wrap Metal Sheet around the Tree Trunk",
            "images": ["tape.jpg"], 
            "text": """
            <div style="display:flex; flex-direction:column; align-items:center; margin-bottom:15px;">
                <img src="/static/bottom.jpg" class="haptic-target apple-bounce" onclick="openModal(this.src)" style="width:180px; height:auto; border-radius:10px;">
                <div class="caption">This is what the bottom of the metal sheet should look like.</div>
            </div>
            From the base of the tree, wrap the metal sheet loosely upwards around the trunk, overlapping the edges slightly. 
            At the bottom of the trunk, make sure the sheet is going upwards, and seal that edge with at least 3 layers of tape.
            <ul style="margin-top:10px;">
                <li>Secure it in place using tape.</li>
            </ul>"""
        },
    {
        "header": "2. Mount the Plates with Hooks",
        "images": ["hook2.jpg", "hook1.jpg"],
        "text": """Insert the hook of each plate over the top of the metal sheet.
        <ul style="margin-top:10px;">
            <li>Position plates on opposing sides.</li>
            <li>Ensure the plates are secure.</li>
        </ul>"""
    },
    {
        "header": "3. Attach Remaining Non-Hook Plates",
        "text": """
        <div style="display:flex; justify-content:center; gap:10px; margin-bottom:1rem; flex-wrap:wrap;">
            <div style="text-align:center;"><img src="/static/side1.jpg" class="haptic-target apple-bounce" onclick="openModal(this.src)" style="width:100px; height:auto; border-radius:8px;"><div class="caption" style="font-size:0.7rem;">Both sides assembled</div></div>
            <div style="text-align:center;"><img src="/static/side2.jpg" class="haptic-target apple-bounce" onclick="openModal(this.src)" style="width:100px; height:auto; border-radius:8px;"><div class="caption" style="font-size:0.7rem;">Side view detail</div></div>
        </div>
        Attach 2 plates to each hook plate:
        Use 2 bolts for each hole, with 4 washers and 2 nuts to secure them. 
        <ul style="margin-top:10px;">
            <li>Make sure the <strong>“U” hole</strong> on each side plate is facing the other side’s <strong>“U” hole</strong>.</li>
        </ul>
        <div style="text-align:center; margin: 1.5rem 0 1rem 0;">
            <img src="/static/middle.jpg" class="haptic-target apple-bounce" onclick="openModal(this.src)" style="width:100px; height:auto; border-radius:8px;">
            <div class="caption" style="font-size:0.7rem;">Middle plates placement</div>
        </div>
        Attach plates in middle gap to complete the barrier.
        <ul style="margin-top: 5px;">
            <li>Use 2 bolts, 4 washers, and 2 nuts for each side of the hole.</li>
            <li>Ensure all bolts and nuts are tightened.</li>
        </ul>"""
    }
]

@app.route("/", methods=["GET", "POST"])
def home():
    is_admin = request.args.get('admin') == ADMIN_PASSWORD
    revs = load_reviews()

    if request.method == "POST":
        if is_admin and request.form.get("action") == "delete":
            idx = int(request.form.get("review_index"))
            if 0 <= idx < len(revs):
                revs.pop(idx)
                save_all_reviews(revs)
            return redirect(url_for('home', admin=ADMIN_PASSWORD))

        name = request.form.get("revName")
        rating = request.form.get("rating")
        text = request.form.get("revText")
        
        if name and rating and text:
            user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            city = get_city_from_ip(user_ip)
            
            revs.insert(0, {
                "name": name, 
                "rating": int(rating), 
                "text": text,
                "city": city 
            })
            save_all_reviews(revs)
            return redirect(url_for('home', reviewed='true'))
        return redirect(url_for('home'))

    # Generate Instructions HTML
    instr_list = []
    for s in INSTRUCTION_STEPS:
        step_html = '<div class="step-card reveal">'
        if "header" in s:
            step_html += f'<div class="step-header">{s["header"]}</div>'
        step_html += f'<div class="step-text">{s["text"]}</div>'
        if s.get("img"):
            cap = f'<div class="caption">{s["caption"]}</div>' if "caption" in s else ""
            step_html += f'''<div style="text-align:center;">
                                <img src="/static/{s["img"]}" class="step-image haptic-target apple-bounce" onclick="openModal(this.src)">
                                {cap}
                             </div>'''
        if s.get("images"):
            imgs = "".join([f'<img src="/static/{i}" class="haptic-target apple-bounce" onclick="openModal(this.src)" style="width:120px; height:auto; border-radius:8px;">' for i in s["images"]])
            step_html += f'<div style="display:flex; justify-content:center; gap:10px; margin-top:1rem; flex-wrap:wrap;">{imgs}</div>'
        step_html += '</div>'
        instr_list.append(step_html)
    instr_html = "".join(instr_list)

    # Generate Reviews HTML
    reviews_list = []
    for i, r in enumerate(revs):
        delete_btn = f"""<form method='POST' style='margin-top:10px;'>
                            <input type='hidden' name='action' value='delete'>
                            <input type='hidden' name='review_index' value='{i}'>
                            <button type='submit' style='background:#ff3b30; color:white; border:none; padding:5px 10px; border-radius:5px; cursor:pointer;'>Delete</button>
                         </form>""" if is_admin else ""
        
        city_tag = f" <span style='font-weight:normal; color:#86868b; font-size:0.85rem;'>• {r.get('city', 'Berkeley')}</span>"
        item = f'''
            <div class="review-item reveal" style="border-bottom:1px solid var(--main-border); padding:15px 0; text-align:left;">
                <div style="font-weight:bold;">{r['name']}{city_tag}</div>
                <div style="color:#ffb400;">{'★'*r['rating']}{'☆'*(5-r['rating'])}</div>
                <div style="margin: 5px 0;">"{r['text']}"</div>
                {delete_btn}
            </div>
        '''
        reviews_list.append(item)
    reviews_html = "".join(reviews_list)

    return render_template_string(f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Stop Squirrel Climb</title>
        <link rel="icon" type="image/png" href="/favicon.png">
        <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.5.1/dist/confetti.browser.min.js"></script>
        <style>
            :root {{ 
                --accent-color: #ff9500; 
                --main-border: #d2d2d7; 
                --bg-color: #f5f5f7; 
                --container-bg: white; 
                --text-color: #1d1d1f; 
                --review-bg: #f9f9f9; 
                --icon-fill: #1d1d1f; 
                --rain-color: #0000FF; 
            }}
            body.dark-mode {{ 
                --bg-color: #161617; 
                --container-bg: #1d1d1f; 
                --text-color: #f5f5f7; 
                --main-border: #424245; 
                --review-bg: #2d2d2f; 
                --icon-fill: #f5f5f7; 
                --rain-color: #5dade2; 
            }}
            body {{ margin: 0; background-color: var(--bg-color); color: var(--text-color); font-family: -apple-system, sans-serif; display: flex; flex-direction: column; align-items: center; transition: 0.3s; scroll-behavior: smooth; overflow-x: hidden; }}
            
            .reveal {{ opacity: 0; transform: translateY(40px); transition: all 0.8s cubic-bezier(0.2, 0.8, 0.2, 1); will-change: transform, opacity; }}
            .reveal.active {{ opacity: 1; transform: translateY(0); }}

            .apple-bounce, .buy-button {{ transition: transform 0.5s cubic-bezier(0.2, 1.1, 0.4, 1.0), box-shadow 0.4s ease, filter 0.3s ease; cursor: pointer; transform-origin: center; will-change: transform; }}
            .apple-bounce:hover, .buy-button:hover {{ transform: scale(1.04) translateY(-3px); filter: brightness(1.05); }}
            .apple-bounce:active, .buy-button:active {{ transform: scale(0.96); filter: brightness(0.9); transition: transform 0.1s; }}
            
            .product-container {{ background: var(--container-bg); border: 2px solid var(--main-border); width: 95%; max-width: 800px; padding: 1.5rem; border-radius: 30px; margin: 20px 0; text-align: center; box-sizing: border-box; position: relative; }}
            
            /* BEFORE/AFTER SLIDER CSS */
            .slider-container {{ position: relative; width: 100%; height: 400px; overflow: hidden; border-radius: 20px; border: 2px solid var(--main-border); background: #eee; }}
            .img-after {{ width: 100%; height: 100%; background-image: url('/static/no.jpg'); background-size: cover; background-position: center; }}
            .img-before {{ position: absolute; top: 0; left: 0; width: 50%; height: 100%; background-image: url('/static/before.jpg'); background-size: cover; background-position: left; border-right: 3px solid white; box-shadow: 10px 0 15px rgba(0,0,0,0.2); pointer-events: none; }}
            #slider-range {{ position: absolute; -webkit-appearance: none; appearance: none; width: 100%; height: 100%; background: transparent; outline: none; margin: 0; cursor: ew-resize; top: 0; left: 0; z-index: 10; }}
            #slider-range::-webkit-slider-thumb {{ -webkit-appearance: none; appearance: none; width: 5px; height: 400px; background: white; }}
            #slider-range::-moz-range-thumb {{ width: 5px; height: 400px; background: white; }}

            .stock-warning {{ display: flex; align-items: center; justify-content: center; gap: 8px; margin-bottom: 5px; }}
            .red-dot {{ height: 10px; width: 10px; background-color: #17de09; border-radius: 50%; display: inline-block; box-shadow: 0 0 10px #17de09; animation: redPulse 1.5s infinite; }}
            @keyframes redPulse {{ 0% {{ opacity: 1; transform: scale(1); }} 50% {{ opacity: 0.4; transform: scale(1.2); }} 100% {{ opacity: 1; transform: scale(1); }} }}
            .stock-text {{ color: #0d0d0c; font-weight: 800; font-size: 0.9rem; }}

            .buy-button {{ 
                display: block; width: 100%; text-decoration: none; 
                background: linear-gradient(90deg, #FF0000, #FF8C00, #00FF00, #00BFFF, #FF0000); 
                background-size: 400% 400%; color: white; padding: 27px 0; 
                filter: saturate(1.5) brightness(1.1); box-shadow: 0 10px 20px rgba(0,0,0,0.1);
                border-radius: 18px; font-weight: 900; font-size: 1.4rem; 
                text-shadow: 0px 2px 4px rgba(0,0,0,0.3); animation: spectrumWave 6s ease infinite; 
                margin-top: 5px; border: none;
            }}
            @keyframes spectrumWave {{ 0% {{ background-position: 0% 50%; }} 50% {{ background-position: 100% 50%; }} 100% {{ background-position: 0% 50%; }} }}

            .dot {{ height: 10px; width: 10px; background-color: #28a745; border-radius: 50%; display: inline-block; animation: blink 1.5s infinite; }}
            @keyframes blink {{ 0% {{ opacity: 1; }} 50% {{ opacity: 0.3; }} 100% {{ opacity: 1; }} }}
            
            .trust-icons {{ display: flex; justify-content: space-around; margin: 2rem 0; gap: 10px; flex-wrap: wrap; }}
            .trust-item {{ flex: 1; min-width: 80px; text-align: center; font-size: 0.65rem; font-weight: 800; color: var(--text-color); letter-spacing: 0.5px; }}
            .trust-icon-circle {{ width: 44px; height: 44px; background: var(--main-border); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 8px; transition: 0.3s; position: relative; }}
            .trust-icon-circle svg {{ width: 26px; height: 26px; fill: var(--icon-fill); }}
            
            .dripping-drop {{ position: fixed; width: 3px; height: 12px; background-color: var(--rain-color); border-radius: 3px; pointer-events: none; z-index: 5000; animation: fallDown 1.2s linear forwards; }}
            @keyframes fallDown {{ 0% {{ transform: translateY(0); opacity: 1; }} 80% {{ opacity: 1; }} 100% {{ transform: translateY(100vh); opacity: 0; }} }}
            
            .product-bio-flex {{ display: flex; align-items: center; gap: 20px; text-align: left; margin: 20px 0; flex-wrap: wrap; justify-content: center; }}
            .bio-text {{ flex: 1; min-width: 280px; font-size: 1rem; line-height: 1.5; }}
            
            .step-card {{ background: var(--container-bg); border-radius: 18px; padding: 1.5rem; margin-bottom: 1.5rem; border: 1.5px solid var(--main-border); text-align: left; }}
            .step-header {{ font-weight: 800; font-size: 1.3rem; margin-bottom: 10px; }}
            .step-image {{ width: 180px; border-radius: 10px; display: block; margin: 15px auto; }}
            
            #progress-bar {{ position: fixed; right: 10px; top: 50%; transform: translateY(-50%); width: 4px; height: 150px; background: var(--main-border); border-radius: 10px; z-index: 1000; }}
            #progress-fill {{ width: 100%; height: 0%; background: var(--accent-color); border-radius: 10px; transition: height 0.1s; }}
            #glide-top {{ position: fixed; bottom: 20px; left: 20px; background: var(--container-bg); border: 2.5px solid var(--main-border); border-radius: 50%; width: 50px; height: 50px; cursor: pointer; display: none; align-items: center; justify-content: center; font-size: 20px; z-index: 1000; }}
            #theme-toggle {{ position: fixed; top: 20px; right: 20px; z-index: 2000; background: var(--container-bg); border: 1.5px solid var(--main-border); width: 45px; height: 45px; border-radius: 50%; cursor: pointer; }}
            
            #modal {{ display: none; position: fixed; z-index: 3000; left: 0; top: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.85); justify-content: center; align-items: center; padding: 20px; box-sizing: border-box; cursor: zoom-out; }}
            #modalImg {{ max-width: 90%; max-height: 80vh; border-radius: 10px; border: 3px solid white; box-shadow: 0 10px 30px rgba(0,0,0,0.5); object-fit: contain; }}
            
            .review-form {{ text-align: left; background: var(--review-bg); padding: 1.5rem; border-radius: 20px; border: 1px solid var(--main-border); margin-top: 2rem; }}
            .review-input {{ width: 100%; padding: 12px; border-radius: 10px; border: 1px solid var(--main-border); margin-bottom: 15px; box-sizing: border-box; }}
            .caption {{ color: #86868b; font-style: italic; margin-top: 4px; text-align: center; }}
            
            #chat-bubble {{ position: fixed; bottom: 25px; right: 25px; width: 60px; height: 60px; background: #007AFF; border-radius: 50%; display: flex; align-items: center; justify-content: center; cursor: pointer; box-shadow: 0 10px 25px rgba(0,122,255,0.4); z-index: 1000; }}
            #chat-window {{ position: fixed; bottom: 95px; right: 25px; width: 300px; background: var(--container-bg); border: 1px solid var(--main-border); border-radius: 20px; box-shadow: 0 15px 40px rgba(0,0,0,0.2); display: none; flex-direction: column; overflow: hidden; z-index: 1000; animation: liquidPop 0.4s ease; }}
            @keyframes liquidPop {{ 0% {{ transform: scale(0.8) translateY(20px); opacity: 0; }} 100% {{ transform: scale(1) translateY(0); opacity: 1; }} }}
            .chat-header {{ background: #007AFF; color: white; padding: 15px; font-weight: bold; }}
            .chat-body {{ padding: 15px; color: var(--text-color); }}
            .chat-input-box {{ width: 100%; padding: 10px; border-radius: 10px; border: 1px solid var(--main-border); box-sizing: border-box; margin-top: 10px; background: var(--bg-color); color: var(--text-color); outline: none; }}
        </style>
    </head>
    <body>
        <button id="theme-toggle">🌙</button>
        <div id="progress-bar"><div id="progress-fill"></div></div>
        <button id="glide-top" onclick="window.scrollTo(0,0)">↑</button>
        <div id="modal" onclick="this.style.display='none'">
            <img id="modalImg" src="">
        </div>

        <div class="product-container">
            <h1>Stop Squirrels from Climbing Your Tree Trunk</h1>
            <div class="shipping-container">
                <span class="dot"></span>
                <span>Ships in 7-14 business days, only to Berkeley</span>
            </div>
            
            <div class="stock-warning">
                <span class="red-dot"></span>
                <span class="stock-text">Shipping Included</span>
            </div>

            <a class="buy-button" href="https://buy.stripe.com/fZubIU6KPgTaci7d0c9oc00" target="_blank">Buy Now - $64.99</a>

            <div class="trust-icons">
                <div class="trust-item">
                    <div class="trust-icon-circle"><svg viewBox="0 0 24 24"><path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z"/></svg></div>
                    SECURE<br>PAYMENT
                </div>
                <div class="trust-item">
                    <div class="trust-icon-circle"><svg viewBox="0 0 24 24"><path d="M12 2L4 5v6.09c0 5.05 3.41 9.76 8 10.91 4.59-1.15 8-5.86 8-10.91V5l-8-3zm6 9.09c0 4-2.55 7.7-6 8.83-3.45-1.13-6-4.82-6-8.83V6.55l6-2.25 6 2.25v4.54z"/><path d="M11 14.17l-1.59-1.59L8 14l3 3 5-5-1.41-1.41L11 14.17z"/></svg></div>
                    QUALITY<br>ASSURED
                </div>
                <div class="trust-item">
                    <div id="rain-btn" class="trust-icon-circle apple-bounce" onclick="startDrip(event)">
                        <svg viewBox="0 0 24 24">
                            <path d="M17.5 15c-0.1 0-0.3 0-0.4 0.1C16.5 12.1 13.9 10 11 10c-2.4 0-4.5 1.5-5.3 3.6-2.1 0.4-3.7 2.2-3.7 4.4 0 2.5 2 4.5 4.5 4.5h11c2.5 0 4.5-2 4.5-4.5s-2-4.5-4.5-4.5z"/>
                            <circle cx="8" cy="21" r="1" fill="var(--rain-color)"/><circle cx="12" cy="22" r="1" fill="var(--rain-color)"/><circle cx="16" cy="21" r="1" fill="var(--rain-color)"/>
                        </svg>
                    </div>
                    WEATHER<br>PROOF
                </div>
                <div class="trust-item">
                    <div class="trust-icon-circle"><svg viewBox="0 0 24 24"><path d="M22.7 19l-9.1-9.1c.9-2.3.4-5-1.5-6.9-2-2-5-2.4-7.4-1.3L9 6 6 9 1.6 4.7C.4 7.1.9 10.1 2.9 12.1c1.9 1.9 4.6 2.4 6.9 1.5l9.1 9.1c.4.4 1 .4 1.4 0l2.3-2.3c.5-.4.5-1.1.1-1.4z"/></svg></div>
                    EASY<br>SETUP
                </div>
            </div>

            <div class="product-bio-flex" style="display: flex; align-items: stretch; gap: 25px; text-align: left; margin: 20px 0; flex-wrap: wrap; justify-content: center;">
                
                <div style="flex: 1.2; min-width: 300px;">
                    <div class="slider-container reveal" id="comparison-slider">
                        <div class="img-after"></div>
                        <div id="before-img" class="img-before"></div>
                        <input type="range" min="0" max="100" value="50" id="slider-range">
                        <div style="position: absolute; bottom: 10px; left: 10px; background: rgba(0,0,0,0.5); color: white; padding: 2px 8px; border-radius: 5px; font-size: 10px; pointer-events: none;">BEFORE</div>
                        <div style="position: absolute; bottom: 10px; right: 10px; background: rgba(0,0,0,0.5); color: white; padding: 2px 8px; border-radius: 5px; font-size: 10px; pointer-events: none;">AFTER</div>
                    </div>
                    <div class="caption">Hover or slide to see the difference</div>
                </div>

                <div style="flex: 1; min-width: 280px; display: flex; flex-direction: column; justify-content: space-between;">
                    <div class="bio-text">
                        <p><strong>Hi, my name is Jaap.</strong></p>
                        <p>I created this product because my dad kept complaining about squirrels raiding our fruit trees and ruining the harvest before we could eat it.</p>
                        <p>To help him out, I designed a custom squirrel-proof barrier and 3D printed the parts myself. It worked well for my family, and I want to share it with your family.</p>
                        <p>I would appreciate any feedback after you try this product yourself.</p>
                    </div>
                    <div style="text-align: right;">
                        <img src="/static/Jaap.jpg" class="apple-bounce" onclick="openModal(this.src)" alt="Jaap" style="width: 120px; height: auto; border-radius: 15px; border: 1.5px solid var(--main-border);">
                    </div>
                </div>
            </div>

            <div id="instructionArea">
                <h2 style="border-bottom: 1px solid var(--main-border); padding-bottom: 10px; margin-top: 1rem;">Installation Instructions</h2>
                {instr_html}
            </div>

            <div class="review-section">
                <h2 style="margin-top:4rem; border-top: 1px solid var(--main-border); padding-top: 20px;">Customer Reviews</h2>
                <div id="thankYouMsg" style="display:none; text-align:center; padding: 20px; background: #e7f5ff; border-radius:15px; color:#228be6; font-weight:bold; margin-bottom: 20px;">
                    🎉 Thank you! Your review has been posted.
                </div>
                <form id="reviewForm" class="review-form" method="POST">
                    <h3>Leave a Review</h3>
                    <input type="text" name="revName" class="review-input" placeholder="Your Name" required>
                    <textarea name="revText" class="review-input" placeholder="Your experience..." rows="3" required></textarea>
                    <select name="rating" class="review-input">
                        <option value="5">★★★★★ (5 Stars)</option>
                        <option value="4">★★★★☆ (4 Stars)</option>
                        <option value="3">★★★☆☆ (3 Stars)</option>
                        <option value="2">★★☆☆☆ (2 Stars)</option>
                        <option value="1">★☆☆☆☆ (1 Star)</option>
                    </select>
                    <button type="submit" style="width:100%; padding:12px; background:var(--text-color); color:var(--container-bg); border-radius:10px; border:none; cursor:pointer; font-weight:bold;">Post Review</button>
                </form>
                <div id="reviewFeed">{reviews_html}</div>
            </div>
        </div>

        <div id="chat-window">
            <div class="chat-header">Support</div>
            <div class="chat-body" id="chat-content">
                <p id="chat-prompt" style="margin:0;">Have a question?</p>
                <input type="text" id="chat-input" class="chat-input-box" placeholder="Type question here...">
                <button id="chat-next-btn" onclick="handleChatFlow()" style="width:100%; margin-top:10px; background:#007AFF; color:white; border:none; padding:10px; border-radius:10px; cursor:pointer; font-weight:bold;">Next</button>
            </div>
        </div>
        <div id="chat-bubble" onclick="toggleChatWindow()">Support</div>

        <script>
            // BEFORE/AFTER SLIDER LOGIC
            const slider = document.getElementById('slider-range');
            const beforeImg = document.getElementById('before-img');
            const sliderContainer = document.getElementById('comparison-slider');

            // Manual Slider Dragging
            slider.addEventListener('input', (e) => {{
                beforeImg.style.width = e.target.value + '%';
            }});

            // HOVER EFFECT LOGIC
            sliderContainer.addEventListener('mousemove', (e) => {{
                // Calculate percentage based on mouse position inside the container
                const rect = sliderContainer.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const percentage = (x / rect.width) * 100;
                
                // Update image width and slider position
                beforeImg.style.width = percentage + '%';
                slider.value = percentage;
            }});

            // Reset to center when mouse leaves (optional)
            sliderContainer.addEventListener('mouseleave', () => {{
                beforeImg.style.width = '50%';
                slider.value = 50;
            }});

            // SCROLL REVEAL
            document.addEventListener("DOMContentLoaded", function() {{
                const observer = new IntersectionObserver((entries) => {{
                    entries.forEach(entry => {{
                        if (entry.isIntersecting) entry.target.classList.add('active');
                    }});
                }}, {{ threshold: 0.1 }});
                document.querySelectorAll('.reveal').forEach(el => observer.observe(el));
            }});

            // REVIEW HANDLING
            const urlParams = new URLSearchParams(window.location.search);
            if (urlParams.get('reviewed') === 'true' || localStorage.getItem('hasReviewed') === 'true') {{
                document.getElementById('reviewForm').style.display = 'none';
                document.getElementById('thankYouMsg').style.display = 'block';
                if (urlParams.get('reviewed') === 'true') {{
                    confetti({{ particleCount: 150, spread: 70, origin: {{ y: 0.6 }} }});
                    localStorage.setItem('hasReviewed', 'true');
                    window.history.replaceState({{}}, document.title, "/");
                }}
            }}

            function startDrip(event) {{
                const btn = document.getElementById('rain-btn');
                const rect = btn.getBoundingClientRect();
                // 10% chance for squirrels, 90% for rain
                const isSquirrelStorm = Math.random() < 0.1;
                
                for(let i=0; i<30; i++) {{
                    setTimeout(() => {{
                        const drop = document.createElement('div');
                        drop.style.position = 'fixed';
                        // Position drops relative to the button
                        drop.style.left = (rect.left + Math.random() * rect.width) + 'px';
                        drop.style.top = rect.top + 'px';
                        drop.style.zIndex = '5000';
                        drop.style.fontSize = isSquirrelStorm ? '30px' : '16px';
                        drop.innerHTML = isSquirrelStorm ? (Math.random() > 0.5 ? '🐿️' : '🥜') : '💧';
                        drop.style.pointerEvents = 'none';
                        
                        // JS Animation API - uses double braces for the f-string
                        drop.animate([
                            {{ transform: 'translateY(0) rotate(0deg)', opacity: 1 }},
                            {{ transform: `translateY(100vh) rotate(${{Math.random() * 360}}deg)`, opacity: 0.3 }}
                        ], {{ 
                            duration: 1500, 
                            easing: 'linear' 
                        }});

                        document.body.appendChild(drop);

                        // Cleanup drop after it falls
                        setTimeout(() => {{
                            drop.remove();
                        }}, 1500);
                    }}, i * 80);
                }}
            }}

            // CHAT FLOW
            let chatStep = 1; let savedQuestion = "";
            function toggleChatWindow() {{
                const win = document.getElementById('chat-window');
                win.style.display = win.style.display === 'flex' ? 'none' : 'flex';
            }}
            function handleChatFlow() {{
                const input = document.getElementById('chat-input');
                const prompt = document.getElementById('chat-prompt');
                const btn = document.getElementById('chat-next-btn');
                if (chatStep === 1) {{
                    if(!input.value.trim()) return;
                    savedQuestion = input.value; input.value = "";
                    prompt.innerText = "What is your email?";
                    input.placeholder = "email@example.com";
                    chatStep = 2;
                }} else {{
                    if(!input.value.trim()) return;
                    btn.innerText = "Sending..."; btn.disabled = true;
                    fetch('/send-support', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{ question: savedQuestion, user_email: input.value }})
                    }}).then(() => {{
                        document.getElementById('chat-content').innerHTML = "<p style='color:#34c759; font-weight:bold;'>Sent! We will reply soon.</p>";
                        setTimeout(toggleChatWindow, 3000);
                    }});
                }}
            }}

           
            // THEME AND PROGRESS
            window.onscroll = () => {{
                let winScroll = document.documentElement.scrollTop;
                let height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
                document.getElementById("progress-fill").style.height = (winScroll / height) * 100 + "%";
                document.getElementById('glide-top').style.display = (winScroll > 300) ? "flex" : "none";
            }};
            document.getElementById('theme-toggle').onclick = () => {{
                document.body.classList.toggle('dark-mode');
                document.getElementById('theme-toggle').innerText = document.body.classList.contains('dark-mode') ? '☀️' : '🌙';
            }};
            function openModal(src) {{
                document.getElementById('modalImg').src = src;
                document.getElementById('modal').style.display = 'flex';
            }}
        </script>
                <a title="Web Analytics" href="https://clicky.com/101498866"><img alt="Clicky" src="//static.getclicky.com/media/links/badge.gif" border="0" /></a>
        <script async data-id="101498866" src="//static.getclicky.com/js"></script>

        
    </body>
    </html>
    """)

if __name__ == "__main__":
    app.run(debug=True)
