from examples import departments


def test_departments():
    result = departments.main()
    assert not result.errors

    deps = result.data["listDepartments"]
    assert len(deps) == 1

    employees = deps[0]["employees"]
    assert len(employees) == 3

    def employee_by_name(employees, name):
        return [e for e in employees if e["name"] == name][0]

    jason = employee_by_name(employees, "Jason")
    carmen = employee_by_name(employees, "Carmen")
    derek = employee_by_name(employees, "Derek")

    # Jason is a manager
    assert jason["teamSize"] == 2
    assert carmen.get("teamSize") is None

    # some sanity checks on optional fields,
    # knowing what the test data is
    assert jason.get("hiredOn") is None
    assert carmen.get("hiredOn") is not None
    assert carmen["salary"]["rating"] == "GS-9"
    assert derek["salary"] is None
