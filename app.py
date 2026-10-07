import cv2
import numpy as np
import streamlit as st
import streamlit.components.v1 as components
import mediapipe as mp

# 1. تهيئة MediaPipe
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

# 2. إعدادات الصفحة
st.set_page_config(
    page_title="AI Sport Scanner",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 3. القائمة الجانبية واللغات
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2964/2964514.png", width=90)
st.sidebar.title("⚡ AI Sport Scanner")

# اختيار اللغة
lang = st.sidebar.radio("🌐 Language / اللغة", ["العربية", "English"])

# قاموس الترجمة للواجهات
TEXTS = {
    "العربية": {
        "title": "⚡ AI Sport Scanner",
        "subtitle": "الماسح الرياضي الذكي وتحليل وضعية التمرين بالذكاء الاصطناعي",
        "select_ex": "اختر التمرين:",
        "exercises": ["Squat (سكوات)", "Bicep Curl (ثني الذراع)", "Push-up (تمرين الضغط)"],
        "reps": "عدد التكرارات",
        "stage": "المرحلة الحالية",
        "angle": "زاوية المفصل",
        "start_cam": "تشغيل الكاميرا والتحليل المباشر",
        "ready": "جاهز للبدء",
        "stand": "قف أمام الكاميرا بوضوح للبدء",
        "up": "أعلى (Up)",
        "down": "أسفل (Down)",
        "good_squat": "ممتاز! انزل للأسفل الآن",
        "great_rep": "عدّة صحيحة وممتازة! 👏",
        "go_lower": "⚠️ انزل أكثر لتحقيق نزول كامل!",
        "curl_up": "ارفع الوزن لأعلى",
        "push_down": "انزل بجسمك للأسفل",
        "push_up": "ضغط ممتاز! ادفع لأعلى",
        "tips_title": "💡 نصائح للتحليل الدقيق:",
        "tips_content": "- ابتعد عن الكاميرا ليظهر جسمك كاملاً.\n- تأكد من وجود إضاءة جيدة.\n- نفذ الحركة ببطء وبشكل متزن."
    },
    "English": {
        "title": "⚡ AI Sport Scanner",
        "subtitle": "Smart AI Exercise Form Scanner & Real-Time Pose Tracking",
        "select_ex": "Select Exercise:",
        "exercises": ["Squat", "Bicep Curl", "Push-up"],
        "reps": "Repetitions",
        "stage": "Current Stage",
        "angle": "Joint Angle",
        "start_cam": "Start Camera & AI Analysis",
        "ready": "Ready",
        "stand": "Stand in front of the camera to start",
        "up": "UP",
        "down": "DOWN",
        "good_squat": "Great! Lower your hips now",
        "great_rep": "Good Repetition! 👏",
        "go_lower": "⚠️ Go lower for full range of motion!",
        "curl_up": "Curl weight upwards",
        "push_down": "Lower your chest",
        "push_up": "Great Push! Drive upwards",
        "tips_title": "💡 Tips for Best Results:",
        "tips_content": "- Make sure your full body is visible.\n- Ensure good lighting.\n- Perform repetitions in controlled speed."
    }
}

t = TEXTS[lang]

# تصميم CSS لتجميل الواجهة وإضافة الإطار المضيء (أخضر / أحمر)
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; }
    .stMetric {
        background-color: #1E232A;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
        border: 1px solid #2D3748;
    }
    .status-card {
        padding: 18px;
        border-radius: 12px;
        margin-top: 10px;
        font-size: 20px;
        font-weight: bold;
        text-align: center;
        transition: all 0.3s ease;
    }
    .good-form { background-color: #1C4532; color: #68D391; border: 2px solid #38A169; box-shadow: 0 0 15px rgba(56, 161, 105, 0.4); }
    .bad-form { background-color: #742A2A; color: #FEB2B2; border: 2px solid #E53E3E; box-shadow: 0 0 15px rgba(229, 62, 62, 0.4); }
    </style>
""", unsafe_allow_html=True)

# 4. اختيار التمرين من القائمة الجانبية
st.sidebar.markdown("---")
exercise = st.sidebar.selectbox(t["select_ex"], t["exercises"])
st.sidebar.markdown("---")
st.sidebar.info(f"{t['tips_title']}\n{t['tips_content']}")

# 5. دالة حساب الزاوية
def calculate_angle(a, b, c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)

    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    
    if angle > 180.0:
        angle = 360.0 - angle
        
    return angle

# دالة إطلاق التنبيهات الصوتية من المتصفح
def play_sound(sound_type):
    if sound_type == "correct":
        js_code = "<script>var ctx = new (window.AudioContext || window.webkitAudioContext)(); var osc = ctx.createOscillator(); osc.type = 'sine'; osc.frequency.value = 800; osc.connect(ctx.destination); osc.start(); setTimeout(function(){ osc.stop(); }, 150);</script>"
    else:
        js_code = "<script>var ctx = new (window.AudioContext || window.webkitAudioContext)(); var osc = ctx.createOscillator(); osc.type = 'sawtooth'; osc.frequency.value = 250; osc.connect(ctx.destination); osc.start(); setTimeout(function(){ osc.stop(); }, 300);</script>"
    components.html(js_code, height=0, width=0)

# 6. الواجهة الرئيسية
st.title(t["title"])
st.caption(t["subtitle"])

col_video, col_stats = st.columns([2.5, 1])

with col_stats:
    st.subheader("📊 " + ("الإحصائيات" if lang == "العربية" else "Metrics"))
    rep_metric = st.metric(label=t["reps"], value="0")
    stage_metric = st.metric(label=t["stage"], value=t["ready"])
    angle_metric = st.metric(label=t["angle"], value="0°")
    feedback_box = st.empty()

with col_video:
    run = st.checkbox(t["start_cam"], value=True)
    FRAME_WINDOW = st.image([])

# 7. تشغيل الفيديو والتحليل
if run:
    cap = cv2.VideoCapture(0)
    counter = 0
    stage = t["ready"]
    feedback = t["stand"]
    form_ok = True
    prev_counter = 0
    prev_form_ok = True

    with mp_pose.Pose(min_detection_confidence=0.7, min_tracking_confidence=0.7) as pose:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                st.error("تعذر الوصول للكاميرا")
                break

            # مرآة الصورة
            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(image)

            current_angle = 0

            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark

                # --- 1. Squat ---
                if "Squat" in exercise:
                    hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
                    knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
                    ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]
                    
                    current_angle = calculate_angle(hip, knee, ankle)
                    
                    if current_angle > 160:
                        stage = t["up"]
                        feedback = t["good_squat"]
                        form_ok = True
                    if current_angle < 90 and stage == t["up"]:
                        stage = t["down"]
                        counter += 1
                        feedback = t["great_rep"]
                        form_ok = True
                    elif current_angle > 90 and current_angle < 120 and stage == t["up"]:
                        feedback = t["go_lower"]
                        form_ok = False

                # --- 2. Bicep Curl ---
                elif "Bicep Curl" in exercise:
                    shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
                    elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
                    wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x, landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]
                    
                    current_angle = calculate_angle(shoulder, elbow, wrist)
                    
                    if current_angle > 150:
                        stage = t["down"]
                        feedback = t["curl_up"]
                        form_ok = True
                    if current_angle < 40 and stage == t["down"]:
                        stage = t["up"]
                        counter += 1
                        feedback = t["great_rep"]
                        form_ok = True

                # --- 3. Push-up ---
                elif "Push-up" in exercise:
                    shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
                    elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
                    wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x, landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]
                    
                    current_angle = calculate_angle(shoulder, elbow, wrist)
                    
                    if current_angle > 160:
                        stage = t["up"]
                        feedback = t["push_down"]
                        form_ok = True
                    if current_angle < 90 and stage == t["up"]:
                        stage = t["down"]
                        counter += 1
                        feedback = t["push_up"]
                        form_ok = True

                # رسم النقاط والوصلات
                mp_drawing.draw_landmarks(
                    image, 
                    results.pose_landmarks, 
                    mp_pose.POSE_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(0, 255, 128), thickness=3, circle_radius=4),
                    mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=2, circle_radius=2)
                )

            # إضافة الإطار الضوئي (أخضر إذا ممتاز / أحمر إذا خطأ)
            border_color = (0, 255, 0) if form_ok else (255, 0, 0)
            cv2.rectangle(image, (0, 0), (w-1, h-1), border_color, 15)

            # مشغل الأصوات التفاعلي
            if counter > prev_counter:
                play_sound("correct")
                prev_counter = counter
            elif not form_ok and prev_form_ok:
                play_sound("wrong")

            prev_form_ok = form_ok

            # تحديث الواجهة التفاعلية
            rep_metric.metric(label=t["reps"], value=str(counter))
            stage_metric.metric(label=t["stage"], value=stage)
            angle_metric.metric(label=t["angle"], value=f"{int(current_angle)}°")
            
            if form_ok:
                feedback_box.markdown(f'<div class="status-card good-form">✅ {feedback}</div>', unsafe_allow_html=True)
            else:
                feedback_box.markdown(f'<div class="status-card bad-form">⚠️ {feedback}</div>', unsafe_allow_html=True)

            FRAME_WINDOW.image(image)

    cap.release()