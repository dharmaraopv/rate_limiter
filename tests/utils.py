class BGTasksForTests:
    def add_task(self, func, *args):
        func(*args)


test_bg_tasks = BGTasksForTests()
