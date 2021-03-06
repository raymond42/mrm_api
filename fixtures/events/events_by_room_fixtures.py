query_all_events_by_room_with_dates = '''
    query{
        allEventsByRoom(calendarId:"andela.com_3630363835303531343031@resource.calendar.google.com",
        startDate:"Jul 10 2018",
        endDate:"Jul 13 2018" ){
            events{
            eventTitle
            roomId
            startTime
            endTime
            }
        }
    }

'''

query_all_events_by_room_with_dates_response = {
    "data": {
        "allEventsByRoom": {
            "events": [
                {
                    "eventTitle": "Onboarding",
                    "roomId": 1,
                    "startTime": "2018-07-11T09:00:00Z",
                    "endTime": "2018-07-11T09:45:00Z",
                }
            ]
        }
    }
}

query_all_events_by_room_without_dates = '''
    query{
        allEventsByRoom(calendarId:"andela.com_3630363835303531343031@resource.calendar.google.com"){
            events{
            eventTitle
            roomId
            startTime
            endTime
            }
        }
    }

'''

query_all_events_by_room_without_dates_response = {
    "data": {
        "allEventsByRoom": {
            "events": [
                {
                    "eventTitle": "Onboarding",
                    "roomId": 1,
                    "startTime": "2018-07-11T09:00:00Z",
                    "endTime": "2018-07-11T09:45:00Z",
                }
            ]
        }
    }
}

query_all_events_by_room_without_callendar_id = '''
    query{
        allEventsByRoom{
            events{
            eventTitle
            roomId
            startTime
            endTime
            }
        }
    }

'''

query_all_events_by_room_with_invalid_calendar_id = '''
    query{
        allEventsByRoom(calendarId:"andela.com_36303638353035313430@resource.calendar.google.com"){
            events{
            eventTitle
            roomId
            startTime
            endTime
            }
        }
    }

'''
