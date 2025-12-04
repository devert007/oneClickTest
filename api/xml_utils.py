import xml.etree.ElementTree as ET
import os
from typing import Dict, List, Optional

XML_FILE_PATH = os.path.join(os.path.dirname(__file__), "tasks.xml")

# Расширенный маппинг для соответствия значений
DIFFICULTY_MAPPING = {
    "Легкий": "Для средних классов",
    "Средний": "Для средних классов", 
    "Сложный": "Для старших классов",
    "Для средних классов": "Для средних классов",
    "Для старших классов": "Для старших классов"
}

TYPE_MAPPING = {
    "Выбор варианта": "multiple_choice",
    "Открытый ответ": "open_ended",
    "multiple_choice": "multiple_choice",
    "open_ended": "open_ended"
}

class Task:
    def __init__(self, question: str, type: str, difficulty: str, answer: str, subject: str, topic: str):
        self.question = question
        self.type = type
        self.difficulty = difficulty
        self.answer = answer
        self.subject = subject
        self.topic = topic

def load_tasks_from_xml() -> Dict[str, Dict[str, List[Task]]]:
    """
    Load tasks from XML file and organize them by subject and topic.
    Returns a dictionary: {subject: {topic: [Task]}}
    """
    tasks_dict = {}
    print(f"Checking XML file at: {XML_FILE_PATH}")
    if not os.path.exists(XML_FILE_PATH):
        print(f"XML file not found at: {XML_FILE_PATH}")
        return tasks_dict

    try:
        tree = ET.parse(XML_FILE_PATH)
        root = tree.getroot()
        print(f"Root element: {root.tag}, Number of subjects: {len(root.findall('subject'))}")

        for subject_elem in root.findall("subject"):
            subject_name = subject_elem.get("name")
            if not subject_name:
                print("Warning: Found subject with no name attribute")
                continue
            tasks_dict[subject_name] = {}
            print(f"Processing subject: {subject_name}")

            for topic_elem in subject_elem.findall("topic"):
                topic_name = topic_elem.get("name")
                if not topic_name:
                    print(f"Warning: Found topic with no name attribute in subject {subject_name}")
                    continue
                tasks_dict[subject_name][topic_name] = []
                print(f"Processing topic: {topic_name}")

                for task_elem in topic_elem.findall("task"):
                    try:
                        question = task_elem.find("question").text if task_elem.find("question") is not None else ""
                        task_type = task_elem.find("type").text if task_elem.find("type") is not None else ""
                        difficulty = task_elem.find("difficulty").text if task_elem.find("difficulty") is not None else ""
                        answer = task_elem.find("answer").text if task_elem.find("answer") is not None else ""
                        
                        if not all([question, task_type, difficulty, answer]):
                            print(f"Warning: Incomplete task in {subject_name}/{topic_name}: {question}")
                            continue
                        
                        # Применяем маппинг для стандартизации значений
                        mapped_difficulty = DIFFICULTY_MAPPING.get(difficulty, difficulty)
                        mapped_type = TYPE_MAPPING.get(task_type, task_type)
                        
                        task = Task(question, mapped_type, mapped_difficulty, answer, subject_name, topic_name)
                        tasks_dict[subject_name][topic_name].append(task)
                        print(f"Added task: {question} (Mapped: {mapped_difficulty}, {mapped_type})")
                    except AttributeError as e:
                        print(f"Error processing task in {subject_name}/{topic_name}: {e}")
                        continue

        print(f"Loaded tasks structure: {list(tasks_dict.keys())}")
        return tasks_dict
    except ET.ParseError as e:
        print(f"XML Parse Error: {e}")
        return {}
    except Exception as e:
        print(f"Unexpected error parsing XML file: {e}")
        return {}

def get_tasks(subject: str, topic: Optional[str] = None, difficulty: Optional[str] = None, task_type: Optional[str] = None, limit: int = None) -> List[Task]:
    """
    Retrieve tasks based on subject, topic, difficulty, and type.
    """
    tasks_dict = load_tasks_from_xml()
    result = []
    print(f"Filtering tasks for subject: '{subject}', topic: '{topic}', difficulty: '{difficulty}', type: '{task_type}', limit: {limit}")

    if subject not in tasks_dict:
        print(f"No tasks found for subject: '{subject}'. Available subjects: {list(tasks_dict.keys())}")
        return result

    for topic_name, tasks in tasks_dict[subject].items():
        if topic and topic_name.lower() != topic.lower():
            continue
        for task in tasks:
            # Нормализуем сравнение (приводим к нижнему регистру и убираем пробелы)
            task_difficulty = task.difficulty.strip().lower() if task.difficulty else ""
            filter_difficulty = difficulty.strip().lower() if difficulty else ""
            
            task_type_normalized = task.type.strip().lower() if task.type else ""
            filter_type = task_type.strip().lower() if task_type else ""
            
            difficulty_match = not difficulty or task_difficulty == filter_difficulty
            type_match = not task_type or task_type_normalized == filter_type
            
            if difficulty_match and type_match:
                result.append(task)
                print(f"Matched task: {task.question} (Difficulty: {task.difficulty}, Type: {task.type})")
            else:
                print(f"Skipped task: {task.question} (Difficulty: '{task.difficulty}' != '{difficulty}', Type: '{task.type}' != '{task_type}')")

    print(f"Total tasks matched: {len(result)}")
    if limit and limit > 0:
        result = result[:limit]
    
    # Warn if no tasks matched due to filters
    if not result and tasks_dict[subject]:
        available_difficulties = set(task.difficulty for tasks in tasks_dict[subject].values() for task in tasks)
        available_types = set(task.type for tasks in tasks_dict[subject].values() for task in tasks)
        print(f"Warning: No tasks matched filters. Available difficulties: {list(available_difficulties)}")
        print(f"Available types: {list(available_types)}")
    
    return result

def get_preview_tasks(subject: str, topic: Optional[str] = None, difficulty: Optional[str] = None, task_type: Optional[str] = None) -> int:
    """
    Get count of available tasks based on filters.
    """
    tasks = get_tasks(subject, topic, difficulty, task_type)
    return len(tasks)