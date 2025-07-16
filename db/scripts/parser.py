import re
import json

class CourseParser:
    def __init__(self):
        pass

    def extract_sentences(self, text, keywords):
        pattern = re.compile(r"([^.]*?(?:" + "|".join(re.escape(kw) for kw in keywords) + r")[^.]*\.)", re.IGNORECASE)
        return [match.group(0).strip() for match in pattern.finditer(text)]

    def extract_course_number(self, course_code):
        match = re.search(r"(\d{4})", course_code)
        return match.group(1) if match else None

    def parse_reqs(self, description, subject_code):
        # Patterns to treat as coreqs (per user instruction)
        coreq_patterns = [
            r"prerequisite or corequisite",
            r"corequisite or prerequisite",
            r"co- or prerequisite",
            r"co- or pre-reqisite",
            r"prerequisite and corequisite",
            r"concurrent",
        ]
        # Patterns to treat as prereqs
        prereq_patterns = [
            r"prerequisite",
            r"must have completed",
            r"requires",
            r"prior completion",
            r"should have completed",
            r"expected to have completed",
            r"expected preparation",
            r"students must have",
        ]
        # Patterns to treat as coreqs (direct)
        direct_coreq_patterns = [
            r"corequisite",
            r"corequisites",
        ]
        # Find all sentences mentioning any of these
        all_patterns = coreq_patterns + prereq_patterns + direct_coreq_patterns
        sentences = self.extract_sentences(description, [p.replace(r"\\", "") for p in all_patterns])
        prereqs = []
        coreqs = []
        for sent in sentences:
            sent_lower = sent.lower()
            # Always treat ambiguous as coreq
            if any(re.search(p, sent_lower) for p in coreq_patterns):
                coreqs.extend(self.parse_req_courses_advanced(sent, subject_code))
            elif any(re.search(p, sent_lower) for p in direct_coreq_patterns):
                coreqs.extend(self.parse_req_courses_advanced(sent, subject_code))
            elif any(re.search(p, sent_lower) for p in prereq_patterns):
                prereqs.extend(self.parse_req_courses_advanced(sent, subject_code))
        return (prereqs if prereqs else None, coreqs if coreqs else None)

    def parse_req_courses_advanced(self, text, subject_code):
        # Clean the initial string
        text = re.sub(r"^[^:]+:", "", text).strip().rstrip(".")
        text = re.sub(r"\s+", " ", text) # Normalize whitespace
        if not text:
            return []
        
        # Start the recursive parsing
        return self._parse_expression(text, subject_code)

    def _parse_expression(self, text, subject_code):
        # Expressions are 'AND' groups, separated by 'and' or ';'
        # We need to be careful not to split inside parentheses
        parts = self._split_outside_parens(text, r"\s+and\s+|\s*;\s*")
        
        groups = []
        for part in parts:
            part = part.strip()
            if not part: continue
            
            # Each part is an 'OR' group (a term)
            or_group = self._parse_term(part, subject_code)
            if or_group:
                groups.append(or_group)
        
        return groups

    def _parse_term(self, text, subject_code):
        # Terms are 'OR' groups
        # Handle parenthetical expressions first by replacing them recursively

        # We need to find the subject code immediately preceding the parenthesis
        def find_subject_for_paren(original_text, paren_match):
            text_before = original_text[:paren_match.start()]
            # Find the last mentioned course code before the parenthesis
            matches = list(re.finditer(r"([A-Z]{2,5})\s+\d{4}[A-Z]?", text_before))
            if matches:
                return matches[-1].group(1)
            return subject_code # Fallback to the default

        def replace_paren_factory(original_text):
            def replace_paren(m):
                # Find the correct subject context for this specific parenthesis
                local_subject = find_subject_for_paren(original_text, m)
                # Recursively parse the content of the parenthesis
                sub_expression = self._parse_expression(m.group(1), local_subject)
                # Flatten the result into a single list of course codes
                flat_list = [course for group in sub_expression for course in group]
                return " or ".join(flat_list)
            return replace_paren

        # Iteratively replace parentheses to handle nesting
        # Because we need the original text to find context, we can't do a simple loop
        if "(" in text:
            # Create a replacer function that has access to the original text
            replacer = replace_paren_factory(text)
            # This only handles one level of nesting properly. A full solution
            # would require a more complex parser.
            text = re.sub(r"\(([^()]+)\)", replacer, text)


        # Normalize 'or' conjunctions
        text = re.sub(r"one of|either", "", text, flags=re.IGNORECASE).strip()
        text = re.sub(r",\s*or\s+", " or ", text, flags=re.IGNORECASE)
        text = re.sub(r",", " or ", text) # Treat commas as 'or' in this context
        
        parts = re.split(r"\s+or\s+", text, flags=re.IGNORECASE)
        
        courses = []
        current_subject = subject_code
        for part in parts:
            part = part.strip()
            if not part: continue
            
            # Identify course codes
            match = re.match(r"([A-Z]{2,5})\s+(\d{4}[A-Z]?)", part)
            if match:
                current_subject = match.group(1)
                courses.append(f"{current_subject} {match.group(2)}")
            else:
                match = re.match(r"(\d{4}[A-Z]?)", part)
                if match:
                    # If no subject is specified, use the last one seen or the default
                    courses.append(f"{current_subject} {match.group(1)}")

        # Special handling for "MATH 1200 (or 1300)" pattern
        # After replacements, this might look like "MATH 1200 1300"
        # The logic needs to be more robust to handle this case
        # Let's refine the regex and combination logic
        final_courses = []
        full_course_pattern = r"([A-Z]{2,5})\s*(\d{4}[A-Z]?)"
        short_course_pattern = r"(\d{4}[A-Z]?)"
        
        tokens = text.split()
        last_subj = subject_code
        for i, token in enumerate(tokens):
            full_match = re.fullmatch(full_course_pattern, token)
            if full_match:
                 last_subj = full_match.group(1)
                 final_courses.append(token)
                 continue
            
            # Is it a full course code split over two tokens? e.g. "CS", "1101"
            if i+1 < len(tokens) and re.fullmatch(r"[A-Z]{2,5}", token):
                next_token_match = re.fullmatch(short_course_pattern, tokens[i+1])
                if next_token_match:
                    last_subj = token
                    final_courses.append(f"{token} {tokens[i+1]}")
                    tokens[i+1] = "" # consume next token
                    continue

            short_match = re.fullmatch(short_course_pattern, token)
            if short_match:
                 final_courses.append(f"{last_subj} {token}")

        return list(dict.fromkeys(final_courses)) if final_courses else []

    def _split_outside_parens(self, text, separator_regex):
        # Helper to split a string by a regex, but not inside parentheses
        parts = []
        paren_level = 0
        current_part = ""
        
        # Use regex to find all separators and parentheses
        tokens = re.split(f"({separator_regex}|\\(|\\))", text)
        
        for token in filter(None, tokens):
            if token == '(':
                paren_level += 1
            elif token == ')':
                paren_level -= 1
            
            if paren_level == 0 and re.match(separator_regex, token):
                parts.append(current_part)
                current_part = ""
            else:
                current_part += token
        
        parts.append(current_part)
        return parts

    def parse_axle_tags(self, description):
        axle_tags = []
        parent_groups = re.findall(r"\(([^()]+)\)", description)
        for group in parent_groups:
            group = group.strip()
            upper_group = group.upper()
            if upper_group.startswith("CORE") or upper_group.startswith("LE"):
                continue
            axle_tags.extend(
                tag.strip()
                for tag in group.split(",")
                if re.fullmatch(r"[A-Z]{1,4}", tag.strip())
            )
        axle_colon_match = re.search(
            r"AXLE:\s*([A-Z]{1,4}(?:\s*,\s*[A-Z]{1,4})*)",
            description,
            re.IGNORECASE
        )
        if axle_colon_match:
            axle_tags.extend(tag.strip().upper() for tag in axle_colon_match.group(1).split(","))
        return list(sorted(set(axle_tags))) if axle_tags else None

    def parse_course(self, course):
        subject_name = course['subject']
        raw_course_code = course.get('course_code')
        title = course.get('course_title')
        description = course.get('description')

        subject_code = None
        course_number = None
        level = None
        course_code = raw_course_code

        if raw_course_code:
            # Match subject code (letters and dashes), then number (4 digits + optional letter)
            match = re.match(r"^([A-Z][A-Z-]*)\s?(\d{4}[A-Z]?)$", raw_course_code)
            if not match:
                # Try to split if no space, e.g. PSY-PC1001 or AADS1101W
                match = re.match(r"^([A-Z][A-Z-]*)(\d{4}[A-Z]?)$", raw_course_code)
            if match:
                subject_code = match.group(1)
                course_number = match.group(2)
                # Normalize course_code to 'SUBJECTCODE NUMBER'
                course_code = f"{subject_code} {course_number}"
                # Extract just the digits for level
                num_match = re.match(r"(\d)", course_number)
                if num_match:
                    level = int(num_match.group(1)) * 1000

        credit_match = re.search(r"\[(\d+(?:-\d+)?)\]", description) if description else None
        credits = credit_match.group(1) if credit_match else None
        
        prereqs, coreqs = self.parse_reqs(description, subject_code) 
        
        axle_tags = self.parse_axle_tags(description) if description else None
        
        return {
            "subject_name": subject_name,
            "course_code": course_code,
            "subject_code": subject_code,
            "course_number": course_number,
            "level": level,
            "title": title,
            "description": description,
            "prereqs": prereqs,
            "coreqs": coreqs,
            "axle": axle_tags,
            "credits": credits,
        }

# --- TESTING ---
def test_req_parser():
    test_cases = [
        # Simple
        ("Prerequisite: MATH 1200.", "MATH", [["MATH 1200"]]),
        ("Prerequisite: 1200.", "MATH", [["MATH 1200"]]),
        ("Prerequisite: MATH 1200 or 1300.", "MATH", [["MATH 1200", "MATH 1300"]]),
        ("Prerequisite: MATH 1200 and 1300.", "MATH", [["MATH 1200"], ["MATH 1300"]]),
        ("Prerequisite: MATH 1200 or 1300 and 1400.", "MATH", [["MATH 1200", "MATH 1300"], ["MATH 1400"]]),
        ("Prerequisite: one of MATH 1200, 1300, 1400.", "MATH", [["MATH 1200", "MATH 1300", "MATH 1400"]]),
        ("Prerequisite: either MATH 1200 or 1300.", "MATH", [["MATH 1200", "MATH 1300"]]),
        # Advanced
        ("Prerequisite: MATH 1200 or 1300, and either CS 1101 or 1104.", "MATH", [["MATH 1200", "MATH 1300"], ["CS 1101", "CS 1104"]]),
        ("Prerequisite: one of MATH 1200, 1300, or 1400, and CS 1101.", "MATH", [["MATH 1200", "MATH 1300", "MATH 1400"], ["CS 1101"]]),
        ("Prerequisite: MATH 1200, 1300, or 1400 and CS 1101 or 1104.", "MATH", [["MATH 1200", "MATH 1300", "MATH 1400"], ["CS 1101", "CS 1104"]]),
        ("Prerequisite: either MATH 1200 or 1300, and either CS 1101 or 1104.", "MATH", [["MATH 1200", "MATH 1300"], ["CS 1101", "CS 1104"]]),
        ("Prerequisite: MATH 1200 and one of CS 1101, 1104.", "MATH", [["MATH 1200"], ["CS 1101", "CS 1104"]]),
        ("Prerequisite: MATH 1200 and CS 1101 or 1104.", "MATH", [["MATH 1200"], ["CS 1101", "CS 1104"]]),
        ("Prerequisite: either MATH 1200 or 1300 and either CS 1101 or 1104.", "MATH", [["MATH 1200", "MATH 1300"], ["CS 1101", "CS 1104"]]),
        ("Prerequisite: MATH 1200, 1300, or 1400, and CS 1101, 1104.", "MATH", [["MATH 1200", "MATH 1300", "MATH 1400"], ["CS 1101", "CS 1104"]]),
    ]
    for desc, subj, expected in test_cases:
        parsed = CourseParser().parse_req_courses_advanced(desc, subj)
        print(f"Description: {desc}\nParsed: {parsed}\nExpected: {expected}\n{'PASS' if parsed == expected else 'FAIL'}\n")

if __name__ == "__main__":
    test_req_parser()

    with open("courses_raw.json") as f:
        raw_courses = json.load(f)
    parsed_courses = [CourseParser().parse_course(course) for course in raw_courses]
    with open("courses_parsed.json", "w") as f:
        json.dump(parsed_courses, f, indent=2)
    print(f"Parsed {len(parsed_courses)} courses and saved to courses_parsed.json")