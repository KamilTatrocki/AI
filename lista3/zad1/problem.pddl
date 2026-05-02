(define (problem logistics-prob1)
  (:domain logistics-extended)
  
  (:objects
    loc_A loc_B loc_C - location
    t1 - truck
    a1 - airplane
    s1 - ship
    p1 p2 - package
  )
  
  (:init
    (at t1 loc_A)
    (at a1 loc_B)
    (at s1 loc_C)
    
    (at p1 loc_A)
    (at p2 loc_B)
    
    (road_route loc_A loc_B)
    (road_route loc_B loc_A)
    
    (flight_route loc_B loc_C)
    (flight_route loc_C loc_B)
    (flight_route loc_A loc_C)
    (flight_route loc_C loc_A)
    
    (sea_route loc_B loc_C)
    (sea_route loc_C loc_B)
    
    (= (distance loc_A loc_B) 100)
    (= (distance loc_B loc_A) 100)
    (= (distance loc_B loc_C) 500)
    (= (distance loc_C loc_B) 500)
    (= (distance loc_A loc_C) 600)
    (= (distance loc_C loc_A) 600)
    
    (= (speed t1) 50)
    (= (speed a1) 250)
    (= (speed s1) 50)
    
    (= (total-cost) 0)
  )
  
  (:goal (and
    (delivered p1 loc_C)
    (delivered p2 loc_A)
  ))
  
  (:metric minimize (+ (* 0.5 (total-time)) (* 0.5 (total-cost))))
)