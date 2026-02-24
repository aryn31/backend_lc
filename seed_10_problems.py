import json
import random
import os
from database import engine, SessionLocal, Base
from models import Problem, TestCase

def generate_problems():
    problems = []

    # --- 1. TWO SUM ---
    tcs_two_sum = [
        {"inputs": [[2, 7, 11, 15], 9], "expected": [0, 1], "is_hidden": False},
        {"inputs": [[3, 2, 4], 6], "expected": [1, 2], "is_hidden": False},
    ]
    for _ in range(23):
        length = random.randint(4, 20)
        base = [random.randint(1000, 2000) for _ in range(length)]
        i, j = random.sample(range(length), 2)
        base[i], base[j] = random.randint(1, 100), random.randint(1, 100)
        tcs_two_sum.append({"inputs": [base, base[i] + base[j]], "expected": sorted([i, j]), "is_hidden": True})
    
    problems.append({
        "title": "Two Sum",
        "description": "Given an array of integers `nums` and an integer `target`, return indices of the two numbers such that they add up to `target`.\n\nYou may assume that each input would have exactly one solution, and you may not use the same element twice.",
        "difficulty": "Easy", "function_name": "two_sum",
        "examples": [{"input": {"nums": [2, 7, 11, 15], "target": 9}, "output": [0, 1]}, {"input": {"nums": [3, 2, 4], "target": 6}, "output": [1, 2]}],
        "constraints": ["2 <= nums.length <= 10^4", "Only one valid answer exists."],
        "test_cases": tcs_two_sum
    })

    # --- 2. CONTAINS DUPLICATE ---
    tcs_dup = [
        {"inputs": [[1, 2, 3, 1]], "expected": True, "is_hidden": False},
        {"inputs": [[1, 2, 3, 4]], "expected": False, "is_hidden": False},
    ]
    for _ in range(23):
        length = random.randint(5, 50)
        has_dup = random.choice([True, False])
        nums = list(range(length))
        if has_dup: nums.append(random.choice(nums))
        random.shuffle(nums)
        tcs_dup.append({"inputs": [nums], "expected": has_dup, "is_hidden": True})

    problems.append({
        "title": "Contains Duplicate",
        "description": "Given an integer array `nums`, return `True` if any value appears at least twice in the array, and return `False` if every element is distinct.",
        "difficulty": "Easy", "function_name": "contains_duplicate",
        "examples": [{"input": {"nums": [1, 2, 3, 1]}, "output": True}, {"input": {"nums": [1, 2, 3, 4]}, "output": False}],
        "constraints": ["1 <= nums.length <= 10^5"],
        "test_cases": tcs_dup
    })

    # --- 3. FIND MAXIMUM ELEMENT ---
    tcs_max = [
        {"inputs": [[1, 5, 3, 9, 2]], "expected": 9, "is_hidden": False},
        {"inputs": [[-1, -5, -3]], "expected": -1, "is_hidden": False},
    ]
    for _ in range(23):
        nums = [random.randint(-1000, 1000) for _ in range(random.randint(5, 50))]
        tcs_max.append({"inputs": [nums], "expected": max(nums), "is_hidden": True})

    problems.append({
        "title": "Find Maximum Element",
        "description": "Given an integer array `nums`, return the maximum element in the array.",
        "difficulty": "Easy", "function_name": "find_maximum",
        "examples": [{"input": {"nums": [1, 5, 3, 9, 2]}, "output": 9}],
        "constraints": ["1 <= nums.length <= 10^5"],
        "test_cases": tcs_max
    })

    # --- 4. VALID PALINDROME STRING ---
    tcs_pal = [
        {"inputs": ["racecar"], "expected": True, "is_hidden": False},
        {"inputs": ["hello"], "expected": False, "is_hidden": False},
    ]
    words = ["level", "radar", "kayak", "madam", "tenet"]
    for _ in range(23):
        is_pal = random.choice([True, False])
        if is_pal:
            w = random.choice(words) + str(random.randint(1,9))
            w = w + w[::-1]
        else:
            w = "abc" + str(random.randint(100,999))
        tcs_pal.append({"inputs": [w], "expected": w == w[::-1], "is_hidden": True})

    problems.append({
        "title": "Valid Palindrome",
        "description": "Given a string `s`, return `True` if it is a palindrome, or `False` otherwise. Assume `s` only contains lowercase English letters and numbers.",
        "difficulty": "Easy", "function_name": "is_palindrome",
        "examples": [{"input": {"s": "racecar"}, "output": True}],
        "constraints": ["1 <= s.length <= 2 * 10^5"],
        "test_cases": tcs_pal
    })

    # --- 5. MISSING NUMBER ---
    tcs_missing = [
        {"inputs": [[3, 0, 1]], "expected": 2, "is_hidden": False},
        {"inputs": [[0, 1]], "expected": 2, "is_hidden": False},
    ]
    for _ in range(23):
        n = random.randint(5, 50)
        nums = list(range(n + 1))
        missing = random.choice(nums)
        nums.remove(missing)
        random.shuffle(nums)
        tcs_missing.append({"inputs": [nums], "expected": missing, "is_hidden": True})

    problems.append({
        "title": "Missing Number",
        "description": "Given an array `nums` containing `n` distinct numbers in the range `[0, n]`, return the only number in the range that is missing from the array.",
        "difficulty": "Easy", "function_name": "missing_number",
        "examples": [{"input": {"nums": [3, 0, 1]}, "output": 2}],
        "constraints": ["n == nums.length", "0 <= nums[i] <= n"],
        "test_cases": tcs_missing
    })

    # --- 6. MAJORITY ELEMENT ---
    tcs_maj = [
        {"inputs": [[3, 2, 3]], "expected": 3, "is_hidden": False},
        {"inputs": [[2, 2, 1, 1, 1, 2, 2]], "expected": 2, "is_hidden": False},
    ]
    for _ in range(23):
        n = random.randint(3, 20)
        maj = random.randint(1, 100)
        nums = [maj] * (n + 1) + [random.randint(101, 200) for _ in range(n - 1)]
        random.shuffle(nums)
        tcs_maj.append({"inputs": [nums], "expected": maj, "is_hidden": True})

    problems.append({
        "title": "Majority Element",
        "description": "Given an array `nums` of size `n`, return the majority element. The majority element is the element that appears more than `n / 2` times.",
        "difficulty": "Easy", "function_name": "majority_element",
        "examples": [{"input": {"nums": [3, 2, 3]}, "output": 3}],
        "constraints": ["The majority element always exists."],
        "test_cases": tcs_maj
    })

    # --- 7. MOVE ZEROES ---
    tcs_zero = [
        {"inputs": [[0, 1, 0, 3, 12]], "expected": [1, 3, 12, 0, 0], "is_hidden": False},
        {"inputs": [[0]], "expected": [0], "is_hidden": False},
    ]
    for _ in range(23):
        n = random.randint(5, 20)
        nums = [random.randint(0, 10) for _ in range(n)]
        expected = [x for x in nums if x != 0] + [0] * nums.count(0)
        tcs_zero.append({"inputs": [nums], "expected": expected, "is_hidden": True})

    problems.append({
        "title": "Move Zeroes",
        "description": "Given an integer array `nums`, return a new array with all `0`'s moved to the end of it while maintaining the relative order of the non-zero elements.",
        "difficulty": "Easy", "function_name": "move_zeroes",
        "examples": [{"input": {"nums": [0, 1, 0, 3, 12]}, "output": [1, 3, 12, 0, 0]}],
        "constraints": ["1 <= nums.length <= 10^4"],
        "test_cases": tcs_zero
    })

    # --- 8. SQUARES OF A SORTED ARRAY ---
    tcs_sq = [
        {"inputs": [[-4, -1, 0, 3, 10]], "expected": [0, 1, 9, 16, 100], "is_hidden": False},
        {"inputs": [[-7, -3, 2, 3, 11]], "expected": [4, 9, 9, 49, 121], "is_hidden": False},
    ]
    for _ in range(23):
        nums = sorted([random.randint(-50, 50) for _ in range(random.randint(5, 20))])
        expected = sorted([x*x for x in nums])
        tcs_sq.append({"inputs": [nums], "expected": expected, "is_hidden": True})

    problems.append({
        "title": "Squares of a Sorted Array",
        "description": "Given an integer array `nums` sorted in non-decreasing order, return an array of the squares of each number sorted in non-decreasing order.",
        "difficulty": "Easy", "function_name": "sorted_squares",
        "examples": [{"input": {"nums": [-4, -1, 0, 3, 10]}, "output": [0, 1, 9, 16, 100]}],
        "constraints": ["nums is sorted in non-decreasing order."],
        "test_cases": tcs_sq
    })

    # --- 9. SINGLE NUMBER ---
    tcs_single = [
        {"inputs": [[2, 2, 1]], "expected": 1, "is_hidden": False},
        {"inputs": [[4, 1, 2, 1, 2]], "expected": 4, "is_hidden": False},
    ]
    for _ in range(23):
        single = random.randint(1, 100)
        pairs = [random.randint(101, 500) for _ in range(random.randint(5, 15))]
        nums = pairs + pairs + [single]
        random.shuffle(nums)
        tcs_single.append({"inputs": [nums], "expected": single, "is_hidden": True})

    problems.append({
        "title": "Single Number",
        "description": "Given a non-empty array of integers `nums`, every element appears twice except for one. Find that single one.",
        "difficulty": "Easy", "function_name": "single_number",
        "examples": [{"input": {"nums": [2, 2, 1]}, "output": 1}],
        "constraints": ["Each element appears twice except for one."],
        "test_cases": tcs_single
    })

    # --- 10. PRODUCT OF ARRAY EXCEPT SELF ---
    tcs_prod = [
        {"inputs": [[1, 2, 3, 4]], "expected": [24, 12, 8, 6], "is_hidden": False},
        {"inputs": [[-1, 1, 0, -3, 3]], "expected": [0, 0, 9, 0, 0], "is_hidden": False},
    ]
    for _ in range(23):
        nums = [random.randint(1, 10) for _ in range(random.randint(4, 10))]
        import math
        total_prod = math.prod(nums)
        expected = [total_prod // x for x in nums]
        tcs_prod.append({"inputs": [nums], "expected": expected, "is_hidden": True})

    problems.append({
        "title": "Product of Array Except Self",
        "description": "Given an integer array `nums`, return an array `answer` such that `answer[i]` is equal to the product of all the elements of `nums` except `nums[i]`.",
        "difficulty": "Medium", "function_name": "product_except_self",
        "examples": [{"input": {"nums": [1, 2, 3, 4]}, "output": [24, 12, 8, 6]}],
        "constraints": ["You must write an algorithm that runs in O(n) time."],
        "test_cases": tcs_prod
    })

    return problems

def run_seed():
    print("🗑️ Deleting old database...")
    if os.path.exists("leetcode.db"):
        os.remove("leetcode.db")
        
    print("🔨 Building fresh database tables...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    problems_data = generate_problems()
    print(f"🚀 Injecting {len(problems_data)} core problems...")

    for prob in problems_data:
        new_problem = Problem(
            title=prob["title"],
            description=prob["description"],
            difficulty=prob["difficulty"],
            function_name=prob["function_name"],
            examples=prob["examples"],
            constraints=prob["constraints"]
        )
        db.add(new_problem)
        db.commit()      
        db.refresh(new_problem)
        
        test_cases_to_insert = []
        for tc in prob["test_cases"]:
            new_tc = TestCase(
                problem_id=new_problem.id,
                inputs=tc["inputs"],
                expected_output=tc["expected"],
                is_hidden=tc["is_hidden"]
            )
            test_cases_to_insert.append(new_tc)
            
        db.add_all(test_cases_to_insert)
        db.commit()
        print(f"✅ Inserted '{new_problem.title}' with {len(test_cases_to_insert)} test cases.")

    print("🎉 Database is fully seeded with the elite Top 10 problems!")
    db.close()

if __name__ == "__main__":
    run_seed()