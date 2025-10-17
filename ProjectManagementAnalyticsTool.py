"""
CPM/PERT Project Management Tool
A comprehensive project management tool implementing
Critical Path Method (CPM) and Program Evaluation and Review Technique (PERT)-
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Activity:
    """Class representing a project activity"""
    id: str
    description: str
    # PERT Times (instead of single duration)
    optimistic: float  # a - Optimistic time
    most_likely: float  # m - Most likely time
    pessimistic: float  # b - Pessimistic time
    dependencies: List[str]

    # Calculated PERT fields
    expected_time: float = 0  # te = (a + 4m + b) / 6
    variance: float = 0  # σ² = ((b - a) / 6)²
    standard_deviation: float = 0  # σ = (b - a) / 6

    # CPM fields (remain the same)
    early_start: float = 0
    early_finish: float = 0
    late_start: float = 0
    late_finish: float = 0
    slack: float = 0

    def __post_init__(self):
        if not self.dependencies:
            self.dependencies = []
        # Calculate PERT values
        self.calculate_pert_times()

    def calculate_pert_times(self):
        """Calculate PERT times and variance"""
        self.expected_time = (self.optimistic + 4 * self.most_likely + self.pessimistic) / 6
        self.variance = ((self.pessimistic - self.optimistic) / 6) ** 2
        self.standard_deviation = (self.pessimistic - self.optimistic) / 6


    @property
    def duration(self):
        """Property for backward compatibility with CPM"""
        return self.expected_time


class Project:
    """Class representing a complete project"""

    def __init__(self, name: str):
        self.name = name
        self.activities = []

    def add_activity(self, activity: Activity):
        self.activities.append(activity)

    def get_activity_by_id(self, activity_id: str) -> Optional[Activity]:
        for activity in self.activities:
            if activity.id == activity_id:
                return activity
        return None

    def display_project(self):
        """Shows all the activities of the project - WITH TIME UNITS"""
        time_unit = getattr(self, 'time_unit', 'days')
        conversion_factor = getattr(self, 'conversion_factor', 1)

        print(f"Project: {self.name}")
        print("=" * 40)
        for activity in self.activities:
            # Convert to original units for display
            if hasattr(activity, 'duration_original'):
                # CPM case - single duration
                duration_display = activity.duration_original
            elif hasattr(activity, 'expected_time'):
                # PERT case - use expected time
                duration_display = activity.expected_time / conversion_factor
            else:
                # Fallback
                duration_display = activity.expected_time

            print(f"  {activity.id}: {activity.description} ({duration_display:.1f} {time_unit})")
            if activity.dependencies:
                print(f"    Depends on: {', '.join(activity.dependencies)}")
            print()

    def calculate_forward_pass(self):
        """Calculate Early Start & Early Finish"""
        print("Calculating Forward Pass...")

        # Find activities without dependencies (start activities)
        start_activities = [a for a in self.activities if not a.dependencies]

        for activity in start_activities:
            activity.early_start = 0
            activity.early_finish = activity.early_start + activity.expected_time

        # Calculate for the rest
        processed = [a.id for a in start_activities]

        while len(processed) < len(self.activities):
            for activity in self.activities:
                if activity.id in processed:
                    continue

                # Check if all dependencies have been calculated
                all_deps_processed = all(
                    dep in processed for dep in activity.dependencies
                )

                if all_deps_processed:
                    # Early Start = max(early_finish of dependencies)
                    dep_finish_times = []
                    for dep_id in activity.dependencies:
                        dep_activity = self.get_activity_by_id(dep_id)
                        if dep_activity:
                            dep_finish_times.append(dep_activity.early_finish)

                    activity.early_start = max(dep_finish_times) if dep_finish_times else 0
                    activity.early_finish = activity.early_start + activity.expected_time
                    processed.append(activity.id)

    def calculate_backward_pass(self):
        """Calculate Late Start & Late Finish"""
        print("Calculating Backward Pass...")

        # Find the project duration
        project_duration = max(act.early_finish for act in self.activities)

        # Find final activities (those that no other activity depends on)
        final_activities = []
        for activity in self.activities:
            is_final = True
            for other_activity in self.activities:
                if activity.id in other_activity.dependencies:
                    is_final = False
                    break
            if is_final:
                final_activities.append(activity)

        # Initialization: All activities have late_finish = project_duration
        for activity in self.activities:
            activity.late_finish = project_duration
            activity.late_start = activity.late_finish - activity.expected_time

        # SIMPLE AND CORRECT: Process in reverse order of early_finish
        activities_by_ef = sorted(self.activities, key=lambda x: x.early_finish, reverse=True)

        for activity in activities_by_ef:
            # Find which activities depend on this one (successors)
            successors = [act for act in self.activities if activity.id in act.dependencies]

            if successors:
                # Late Finish = min(late_start of successors)
                successor_late_starts = [succ.late_start for succ in successors]
                new_late_finish = min(successor_late_starts)

                # Update only if it gives an earlier finish time
                if new_late_finish < activity.late_finish:
                    activity.late_finish = new_late_finish
                    activity.late_start = activity.late_finish - activity.expected_time

    def calculate_slack(self):
        """Calculate Slack Time"""
        print("Calculating Slack Time...")

        for activity in self.activities:
            activity.slack = activity.late_start - activity.early_start
            # Fix floating point precision issues
            if abs(activity.slack) < 0.001:
                activity.slack = 0.0

    def identify_critical_path(self):
        """Find Critical Path"""
        critical_activities = [act for act in self.activities if act.slack == 0]

        # Sort by early_start
        critical_activities.sort(key=lambda x: x.early_start)

        return critical_activities

    def run_cpm_analysis(self):
        """Execute complete CPM analysis"""
        print("\n" + "=" * 50)
        print("STARTING CPM ANALYSIS")
        print("=" * 50)

        self.calculate_forward_pass()
        self.calculate_backward_pass()
        self.calculate_slack()

        print("CPM Analysis Completed!")

    def display_cpm_results(self):
        """Shows cpm results - WITH TIME UNITS"""
        time_unit = getattr(self, 'time_unit', 'days')
        conversion_factor = getattr(self, 'conversion_factor', 1)

        print(f"CPM RESULTS for '{self.name}'")
        print("=" * 60)
        print(f"{'ID':<4} {'Description':<15} {'ES':<6} {'EF':<6} {'LS':<6} {'LF':<6} {'Slack':<8} {'Critical':<10}")
        print("-" * 60)

        critical_activities = self.identify_critical_path()
        critical_ids = [act.id for act in critical_activities]

        for activity in sorted(self.activities, key=lambda x: x.early_start):
            is_critical = "YES" if activity.id in critical_ids else "NO"

            # Convert to original units for display
            es_display = activity.early_start / conversion_factor
            ef_display = activity.early_finish / conversion_factor
            ls_display = activity.late_start / conversion_factor
            lf_display = activity.late_finish / conversion_factor
            slack_display = activity.slack / conversion_factor

            # Fix -0.0 display issue
            display_es = es_display if es_display >= 0 else 0.0
            display_ls = ls_display if ls_display >= 0 else 0.0
            display_slack = slack_display if slack_display >= 0 else 0.0

            print(f"{activity.id:<4} {activity.description:<15} {display_es:<6.1f} {ef_display:<6.1f} "
                  f"{display_ls:<6.1f} {lf_display:<6.1f} {display_slack:<8.1f} {is_critical:<10}")

        # Critical Path
        project_duration = max(act.early_finish for act in self.activities) / conversion_factor
        print(f"\n🔴 CRITICAL PATH: {' → '.join([act.id for act in critical_activities])}")
        print(f"Total Project Duration: {project_duration:.1f} {time_unit}")


def create_sample_project():
    """Making a simple project for testing - WITH DAYS AS DEFAULT"""

    project = Project("Software Development Project")

    # Set default time unit to days
    project.time_unit = "days"
    project.conversion_factor = 1

    activities = [
        Activity("A", "Requirements", 3, 5, 7, []),
        Activity("B", "Design", 4, 6, 8, ["A"]),
        Activity("C", "Development", 8, 10, 14, ["B"]),
        Activity("D", "Testing", 3, 4, 6, ["C"])
    ]

    for activity in activities:
        # Store original duration info for display
        activity.duration_original = activity.most_likely  # Use most_likely as the single duration
        activity.time_unit = "days"
        project.add_activity(activity)

    return project


def manual_input_project():
    """User manually inputs data (Single time estimate) - WITH TIME UNITS"""

    print("MANUAL PROJECT INPUT (Single Time)")
    print("====================================")

    # User selects measurement unit
    time_unit, conversion_factor = select_time_unit()

    print(f"\nUsing time unit: {time_unit}")

    project_name = input("Project name: ").strip()
    project = Project(project_name)

    # Store time unit info in project
    project.time_unit = time_unit
    project.conversion_factor = conversion_factor

    activities = []

    while True:
        print(f"\n--- Activity #{len(activities) + 1} ---")

        # ID
        activity_id = input("Activity ID (e.g., A, B, T1): ").strip().upper()
        if not activity_id:
            print("Activity ID is required!")
            continue

        # Description
        description = input("Activity description: ").strip()
        if not description:
            description = f"Activity {activity_id}"

        # Duration
        try:
            duration = float(input(f"Duration (in {time_unit}): ").strip())
            duration_days = duration * conversion_factor
        except ValueError:
            print("Please enter a valid number!")
            continue

        # Dependencies
        deps_input = input("Dependencies (comma-separated IDs, or press Enter if none): ").strip()
        if deps_input:
            dependencies = [dep.strip().upper() for dep in deps_input.split(",")]
        else:
            dependencies = []

        # Create activity (using single time as all three estimates)
        activity = Activity(activity_id, description, duration_days, duration_days, duration_days, dependencies)

        # Store original unit info
        activity.duration_original = duration
        activity.time_unit = time_unit

        activities.append(activity)

        # Ask if continue with validation
        while True:
            continue_input = input("\nAdd another activity? (y/n): ").strip().lower()
            if continue_input in ['y', 'n']:
                break
            else:
                print("Please enter 'y' for yes or 'n' for no")

        if continue_input != 'y':
            break

    # Add all activities to project
    for activity in activities:
        project.add_activity(activity)

    return project


def manual_input_project_pert():
    """User manually inputs data - WITH TIME UNITS"""

    print("PERT PROJECT INPUT")
    print("====================")

    # User selects measurement unit
    time_unit, conversion_factor = select_time_unit()

    print(f"\nUsing time unit: {time_unit}")
    print("For each activity, enter three time estimates:")
    print("  🟢 Optimistic (a) - Best case scenario")
    print("  🟡 Most Likely (m) - Normal scenario")
    print("  🔴 Pessimistic (b) - Worst case scenario")
    print()

    project_name = input("Project name: ").strip()
    project = Project(project_name)

    # Store time unit info in project
    project.time_unit = time_unit
    project.conversion_factor = conversion_factor

    activities = []

    while True:
        print(f"\n--- Activity #{len(activities) + 1} ---")

        # ID
        activity_id = input("Activity ID (e.g., A, B, T1): ").strip().upper()
        if not activity_id:
            print("Activity ID is required!")
            continue

        # Description
        description = input("Activity description: ").strip()
        if not description:
            description = f"Activity {activity_id}"

        # PERT Times
        try:
            print(f"Time Estimates (in {time_unit}):")
            optimistic = float(input("  Optimistic time (a): ").strip())
            most_likely = float(input("  Most likely time (m): ").strip())
            pessimistic = float(input("  Pessimistic time (b): ").strip())

            # Convert to days for internal calculations
            optimistic_days = optimistic * conversion_factor
            most_likely_days = most_likely * conversion_factor
            pessimistic_days = pessimistic * conversion_factor

            # Validation
            if not (optimistic_days <= most_likely_days <= pessimistic_days):
                print("Times must be: a ≤ m ≤ b")
                continue
            if optimistic_days < 0:
                print("Times must be positive")
                continue

        except ValueError:
            print("Please enter valid numbers!")
            continue

        # Dependencies
        deps_input = input("Dependencies (comma-separated IDs, or press Enter if none): ").strip()
        if deps_input:
            dependencies = [dep.strip().upper() for dep in deps_input.split(",")]
        else:
            dependencies = []

        # Create PERT activity (store in days internally)
        activity = Activity(activity_id, description, optimistic_days, most_likely_days, pessimistic_days, dependencies)

        # Store the original unit values for display
        activity.optimistic_original = optimistic
        activity.most_likely_original = most_likely
        activity.pessimistic_original = pessimistic
        activity.time_unit = time_unit

        activities.append(activity)

        # Show calculated expected time in original units
        expected_original = activity.expected_time / conversion_factor
        std_dev_original = activity.standard_deviation / conversion_factor

        print(f"Expected time: {expected_original:.1f} {time_unit}")
        print(f"Standard deviation: ±{std_dev_original:.1f} {time_unit}")

        # Ask if continue with validation
        while True:
            continue_input = input("\nAdd another activity? (y/n): ").strip().lower()
            if continue_input in ['y', 'n']:
                break
            else:
                print("Please enter 'y' for yes or 'n' for no")

        if continue_input != 'y':
            break

    # Add all activities to project
    for activity in activities:
        project.add_activity(activity)

    return project


def display_pert_project_summary(project):
    """Display project summary - WITH TIME UNITS"""
    time_unit = getattr(project, 'time_unit', 'days')
    conversion_factor = getattr(project, 'conversion_factor', 1)

    print(f"PERT Project Summary: '{project.name}'")
    print("=" * 70)
    print(
        f"{'ID':<4} {'Description':<15} {'Opt':<6} {'ML':<6} {'Pess':<6} {'Expected':<9} {'Std Dev':<8} {'Dependencies':<15}")
    print("-" * 70)

    for activity in project.activities:
        deps_str = ", ".join(activity.dependencies) if activity.dependencies else "None"

        # Convert back to original units for display
        if hasattr(activity, 'optimistic_original'):
            opt = activity.optimistic_original
            ml = activity.most_likely_original
            pess = activity.pessimistic_original
            expected = activity.expected_time / conversion_factor
            std_dev = activity.standard_deviation / conversion_factor
        else:
            # Fallback for old projects without unit info
            opt = activity.optimistic
            ml = activity.most_likely
            pess = activity.pessimistic
            expected = activity.expected_time
            std_dev = activity.standard_deviation

        print(f"{activity.id:<4} {activity.description:<15} {opt:<6.1f} {ml:<6.1f} "
              f"{pess:<6.1f} {expected:<9.1f} {std_dev:<8.1f} {deps_str:<15}")

    print(f"All times are in {time_unit}")


def display_pert_results(project):
    """Display PERT-specific results - WITH TIME UNITS"""
    time_unit = getattr(project, 'time_unit', 'days')
    conversion_factor = getattr(project, 'conversion_factor', 1)

    print(f"PERT ANALYSIS RESULTS")
    print("=" * 50)

    # Project variance and standard deviation - FIXED
    critical_path = project.identify_critical_path()


    total_variance = 0
    for activity in critical_path:
        # Convert variance from days² to original units²
        variance_display = activity.variance / (conversion_factor ** 2)
        print(f"   {activity.id}: variance = {variance_display:.4f}")
        total_variance += variance_display

    project_variance = total_variance
    project_std_dev = project_variance ** 0.5
    project_duration = max(act.early_finish for act in project.activities)

    # Convert to original units for display
    project_duration_display = project_duration / conversion_factor
    project_std_dev_display = project_std_dev

    print(f"Project Statistics:")
    print(f"   • Expected Project Duration: {project_duration_display:.1f} {time_unit}")
    print(f"   • Project Variance: {project_variance:.2f}")
    print(f"   • Project Standard Deviation: ±{project_std_dev_display:.2f} {time_unit}")

    # Probability calculations
    print(f"Probability Analysis:")

    # Ask user for target date
    try:
        target_date = float(input(f"Enter target completion date (in {time_unit}): ").strip())
        target_date_days = target_date * conversion_factor

        # Z-score calculation - (convert everything to days for calculation)
        project_std_dev_days = project_std_dev * conversion_factor
        z_score = (target_date_days - project_duration) / project_std_dev_days if project_std_dev_days > 0 else 0

        # Simple probability estimation
        if z_score >= 2:
            probability = "> 95%"
        elif z_score >= 1:
            probability = "~ 85%"
        elif z_score >= 0:
            probability = "~ 50%"
        elif z_score >= -1:
            probability = "~ 15%"
        else:
            probability = "< 5%"

        print(f"   • Probability to finish in {target_date:.1f} {time_unit}: {probability}")
        print(f"   • Z-score: {z_score:.2f}")

    except ValueError:
        print("   • Probability analysis skipped (invalid input)")

    # Risk assessment
    print(f"Risk Assessment:")
    optimistic_duration = sum(activity.optimistic for activity in critical_path) / conversion_factor
    pessimistic_duration = sum(activity.pessimistic for activity in critical_path) / conversion_factor

    print(f"   • Best-case scenario: {optimistic_duration:.1f} {time_unit}")
    print(f"   • Worst-case scenario: {pessimistic_duration:.1f} {time_unit}")

    confidence_low = (project_duration - project_std_dev * conversion_factor) / conversion_factor
    confidence_high = (project_duration + project_std_dev * conversion_factor) / conversion_factor
    print(f"   • Confidence interval: {confidence_low:.1f} to {confidence_high:.1f} {time_unit}")


def validate_project(project):
    """Check if the project is valid"""

    # Check for activities without ID
    for activity in project.activities:
        if not activity.id:
            print(f"Activity without ID found!")
            return False

    #Check for circular dependencies
    try:
        project.run_cpm_analysis()
        return True
    except Exception as e:
        print(f"Project validation failed: {e}")
        return False


def display_input_menu():
    """Display data input menu"""

    print("DATA INPUT OPTIONS")
    print("====================")
    print("1. Manual CPM Input (Single time estimate)")
    print("2. Manual PERT Input (Three time estimates)")
    print("3. Use Sample Project")
    print("4. Import from Excel (coming soon)")
    print("5. Exit")

    return input("\nSelect option (1-5): ").strip()


def select_time_unit():
    """The user selects a time unit
"""
    print("\n⏱️  SELECT TIME UNIT")
    print("===================")
    print("1. Hours")
    print("2. Days")
    print("3. Weeks")
    print("4. Months")
    print("5. Years")


    units = {
        "1": ("hours", 1 / 24),
        "2": ("days", 1),
        "3": ("weeks", 7),
        "4": ("months", 30),
        "5": ("years", 365)
    }
    while True:
        choice = input("Select time unit (1-5): ").strip()
        if choice in units:
            return units[choice]
        else:
            print("Please enter a number between 1 and 5")


    return units.get(choice, ("days", 1))


def display_with_units(value, conversion_factor, time_unit, decimals=1):
    """Converts and displays values with the correct units
"""
    return f"{value / conversion_factor:.{decimals}f} {time_unit}"



def main():
    """Main function of the program"""

    print("CPM/PERT Project Management Tool")
    print("===================================")

    while True:
        choice = display_input_menu()

        if choice == "1":
            # Manual Input (Single time - CPM)
            project = manual_input_project()

            if validate_project(project):
                print(f"Project '{project.name}' created successfully!")
                print(f"   Activities: {len(project.activities)}")

                # Show project summary
                project.display_project()

                # Run CPM analysis
                while True:
                    run_analysis = input("\nRun CPM analysis? (y/n): ").strip().lower()
                    if run_analysis in ['y', 'n']:
                        break
                    else:
                        print("Please enter 'y' for yes or 'n' for no")

                if run_analysis == 'y':
                    project.run_cpm_analysis()
                    project.display_cpm_results()

        elif choice == "2":
            # PERT Input (Three times)
            project = manual_input_project_pert()

            if validate_project(project):
                print(f"PERT Project '{project.name}' created successfully!")
                print(f"   Activities: {len(project.activities)}")

                # Show project summary with PERT info
                display_pert_project_summary(project)

                # Performing CPM/PERT analysis
                while True:
                    run_analysis = input("\nRun CPM analysis? (y/n): ").strip().lower()
                    if run_analysis in ['y', 'n']:
                        break
                    else:
                        print("Please enter 'y' for yes or 'n' for no")

                if run_analysis == 'y':
                    project.run_cpm_analysis()
                    project.display_cpm_results()
                    # Add PERT-specific results
                    display_pert_results(project)

        elif choice == "3":
            # Sample Project
            project = create_sample_project()
            print(f"Sample project '{project.name}' loaded!")
            project.display_project()

            # Automatic CPM analysis
            project.run_cpm_analysis()
            project.display_cpm_results()
            display_pert_results(project)

        elif choice == "4":
            print("Excel import feature coming soon...")
            print("For now, please use manual input or sample project.")

        elif choice == "5":
            print("Thank you for using CPM/PERT Tool!")
            break

        else:
            print("Invalid option! Please choose 1-5.")

        while True:
            continue_choice = input("\nContinue with another project? (y/n): ").strip().lower()
            if continue_choice in ['y', 'n']:
                break
            else:
                print("Please enter 'y' for yes or 'n' for no")

        if continue_choice != 'y':
            print("👋 Goodbye!")
            break


if __name__ == "__main__":
    main()