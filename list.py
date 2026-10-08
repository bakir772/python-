import os
FILENAME = "tasks.txt"
def load_tasks():
    """تحميل المهام المحفوظة مسبقاً من الملف النصي"""
    if not os.path.exists(FILENAME):
        return []
    with open(FILENAME, "r", encoding="utf-8") as file:
        tasks = [line.strip() for line in file.readlines()]
    return tasks
def save_tasks(tasks):
    """حفظ المهام الحالية في الملف النصي"""
    with open(FILENAME, "w", encoding="utf-8") as file:
        for task in tasks:
            file.write(task + "\n")
def show_tasks(tasks):
    """عرض قائمة المهام الحالية"""
    if not tasks:
        print("\nقائمة المهام فارغة حالياً! 📋")
    else:
        print("\n--- قائمة المهام الخاصة بك ---")
        for index, task in enumerate(tasks, start=1):
            print(f"{index}. {task}")
    print("-" * 30)
def add_task(tasks):
    """إضافة مهمة جديدة"""
    task = input("أدخل عنوان المهمة الجديدة: ").strip()
    if task:
        tasks.append(task)
        save_tasks(tasks)
        print(f"تمت إضافة المهمة: ( {task} ) بنجاح! ✅")
    else:
        print("لا يمكن إضافة مهمة فارغة! ⚠️")
def delete_task(tasks):
    """حذف مهمة مكتملة أو غير مطلوبة"""
    show_tasks(tasks)
    if not tasks:
        return
    try:
        choice = int(input("أدخل رقم المهمة التي تريد حذفها: "))
        if 1 <= choice <= len(tasks):
            removed = tasks.pop(choice - 1)
            save_tasks(tasks)
            print(f"تم حذف المهمة: ( {removed} ) بنجاح! 🗑️")
        else:
            print("رقم المهمة غير صحيح! ❌")
    except ValueError:
        print("الرجاء إدخال رقم صحيح! ⚠️")
def main():
    """الدالة الرئيسية لتشغيل البرنامج"""
    tasks = load_tasks()
    while True:
        print("\n=== نظام إدارة المهام ===")
        print("1. عرض المهام")
        print("2. إضافة مهمة جديدة")
        print("3. حذف مهمة")
        print("4. خروج")
        choice = input("اختر رقماً من القائمة (1-4): ").strip()
        if choice == "1":
            show_tasks(tasks)
        elif choice == "2":
            add_task(tasks)
        elif choice == "3":
            delete_task(tasks)
        elif choice == "4":
            print("شكراً لاستخدامك مدير المهام. إلى اللقاء! 👋")
            break
        else:
            print("اختيار غير صحيح، الرجاء المحاولة مرة أخرى. ⚠️")
if __name__ == "__main__":
    main()