import xml.etree.ElementTree as ET
import os
from typing import Dict, List, Optional

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
            if not subject_name:
                continue
            tasks_dict[subject_name] = {}

            for topic_elem in subject_elem.findall("topic"):
                topic_name = topic_elem.get("name")
                if not topic_name:
                    continue
                tasks_dict[subject_name][topic_name] = []

                for task_elem in topic_elem.findall("task"):
                    try:
                        question = task_elem.find("question").text if task_elem.find("question") is not None else ""
                        task_type = task_elem.find("type").text if task_elem.find("type") is not None else ""
                        difficulty = task_elem.find("difficulty").text if task_elem.find("difficulty") is not None else ""
                        answer = task_elem.find("answer").text if task_elem.find("answer") is not None else ""
                        if not all([question, task_type, difficulty, answer]):
                            print(f"Warning: Incomplete task in {subject_name}/{topic_name}: {question}")
                            continue
                        task = Task(question, task_type, difficulty, answer, subject_name, topic_name)
                        tasks_dict[subject_name][topic_name].append(task)
                    except AttributeError as e:
                        continue

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
  print(f"Filtering tasks for subject: {subject}, topic: {topic}, difficulty: {difficulty}, type: {task_type}, limit: {limit}")

  if subject not in tasks_dict:
      print(f"No tasks found for subject: {subject}. Available subjects: {list(tasks_dict.keys())}")
      return result

  for topic_name, tasks in tasks_dict[subject].items():
      if topic and topic_name.lower() != topic.lower():
          continue
      for task in tasks:
          difficulty_match = difficulty is None or task.difficulty.lower() == difficulty.lower()
          type_match = task_type is None or task.type.lower() == task_type.lower()
          
          if difficulty_match and type_match:
              result.append(task)
              print(f"Matched task: {task.question} (Difficulty: {task.difficulty}, Type: {task.type})")
          else:
              print(f"Skipped task: {task.question} (Difficulty: {task.difficulty} != {difficulty}, Type: {task.type} != {task_type})")

  if limit:
      result = result[:limit]
  
  # Warn if no tasks matched due to filters
      
  return result


def get_preview_tasks(subject: str, topic: Optional[str] = None, difficulty: Optional[str] = None, task_type: Optional[str] = None) -> List[Task]:
  """
    Retrieve tasks based on subject, topic, difficulty, and type.
    """
  tasks_dict = load_tasks_from_xml()
  result = []

  if subject not in tasks_dict:
      return result

  for topic_name, tasks in tasks_dict[subject].items():
      if topic and topic_name.lower() != topic.lower():
          continue
      for task in tasks:
          difficulty_match = difficulty is None or task.difficulty.lower() == difficulty.lower()
          type_match = task_type is None or task.type.lower() == task_type.lower()
          
          if difficulty_match and type_match:
              result.append(task)

  return len(result)