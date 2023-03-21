"""
Copyright 2022-2023 Wargaming.net

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import time
import cProfile
from clacks.tests import ClacksTestCase


# ----------------------------------------------------------------------------------------------------------------------
class StressTest(ClacksTestCase):

    # ------------------------------------------------------------------------------------------------------------------
    def test_high_package_nr(self):
        package_nr = 1000

        profile = cProfile.Profile()
        profile.enable()

        response_times = list()
        start = time.time()

        for _ in range(package_nr):
            a = time.time()
            self.client.list_commands()
            b = time.time()
            response_times.append((b - a))

        end = time.time()

        profile.disable()

        profile.print_stats(sort='cumtime')

        print('Took %s seconds for %s packages' % (end - start, package_nr))
        print('average response time is %s seconds' % (sum(response_times) / float(len(response_times))))
