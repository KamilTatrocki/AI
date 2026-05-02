(define (problem transport-problem)
  (:domain transport-domain)
  (:objects
    city-a port-a airport-a - location
    city-b port-b airport-b - location
    t1 - truck
    a1 - airplane
    s1 - ship
    p1 p2 - package
  )
  (:init
    (= (total-cost) 0)

    (connected-road city-a port-a)
    (connected-road port-a city-a)
    (connected-road city-a airport-a)
    (connected-road airport-a city-a)
    (connected-road city-b port-b)
    (connected-road port-b city-b)
    (connected-road city-b airport-b)
    (connected-road airport-b city-b)
    (connected-road city-a city-b)
    (connected-road city-b city-a)

    (connected-air airport-a airport-b)
    (connected-air airport-b airport-a)

    (connected-water port-a port-b)
    (connected-water port-b port-a)

    (= (distance city-a port-a) 20)
    (= (distance port-a city-a) 20)
    (= (distance city-a airport-a) 30)
    (= (distance airport-a city-a) 30)
    (= (distance city-b port-b) 15)
    (= (distance port-b city-b) 15)
    (= (distance city-b airport-b) 25)
    (= (distance airport-b city-b) 25)

    (= (distance city-a city-b) 500)
    (= (distance city-b city-a) 500)
    (= (distance airport-a airport-b) 450)
    (= (distance airport-b airport-a) 450)
    (= (distance port-a port-b) 600)
    (= (distance port-b port-a) 600)

    (= (speed t1) 60)
    (= (fuel-cost t1) 2)

    (= (speed a1) 800)
    (= (fuel-cost a1) 15)

    (= (speed s1) 30)
    (= (fuel-cost s1) 1)

    (at t1 city-a)
    (at a1 airport-a)
    (at s1 port-a)

    (at p1 city-a)
    (at p2 port-a)
  )
  (:goal (and
    (at p1 city-b)
    (at p2 airport-b)
  ))
  (:metric minimize (total-cost))
)