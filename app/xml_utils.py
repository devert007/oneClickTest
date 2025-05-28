import xml.etree.ElementTree as ET
import os
from typing import List, Dict, Optional

XML_FILE_PATH = os.path.join(os.path.dirname(__file__), "tasks.xml")

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
    if not os.path.exists(XML_FILE_PATH):
        return tasks_dict

    try:
        tree = ET.parse(XML_FILE_PATH)
        root = tree.getroot()

        for subject_elem in root.findall("subject"):
            subject_name = subject_elem.get("name")
            tasks_dict[subject_name] = {}

            for topic_elem in subject_elem.findall("topic"):
                topic_name = topic_elem.get("name")
                tasks_dict[subject_name][topic_name] = []

                for task_elem in topic_elem.findall("task"):
                    question = task_elem.find("question").text
                    task_type = task_elem.find("type").text
                    difficulty = task_elem.find("difficulty").text
                    answer = task_elem.find("answer").text
                    task = Task(question, task_type, difficulty, answer, subject_name, topic_name)
                    tasks_dict[subject_name][topic_name].append(task)

        return tasks_dict
    except Exception as e:
        print(f"Error parsing XML file: {e}")
        return {}

def get_tasks(subject: str, topic: Optional[str] = None, difficulty: Optional[str] = None, task_type: Optional[str] = None, limit: int = None) -> List[Task]:
    """
    Retrieve tasks based on subject, topic, difficulty, and type.
    """
    tasks_dict = load_tasks_from_xml()
    result = []

    if subject not in tasks_dict:
        return result

    for topic_name, tasks in tasks_dict[subject].items():
        if topic and topic_name != topic:
            continue
        for task in tasks:
            if (difficulty and task.difficulty != difficulty) or (task_type and task.type != task_type):
                continue
            result.append(task)

    return result[:limit] if limit else result