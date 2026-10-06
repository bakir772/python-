import time
print("welcome to the Pomodoro timer!")
# نطلب من المستخدم إدخال الوقت
mins = int(input("enter time in minutes: "))
# حساب إجمالي الثواني (تم تصحيح الإملاء)
total_seconds = mins * 60
# نبدأ العد التنازلي
while total_seconds > 0:
  # لحساب الدقائق
  mins = total_seconds // 60
  # لحساب الثواني
  secs = total_seconds % 60
  # تنسيق شكل الوقت
  clock = f"{mins:02d}:{secs:02d}"
  print(f"\r time remaining: {clock}", end="")
  # تأخذ ثانية للإكمال وثبات المؤشر
  time.sleep(1)
  total_seconds -= 1
print("\n time's up, take a break!")