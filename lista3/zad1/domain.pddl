(define (domain logistics-extended)
  (:requirements :strips :typing :negative-preconditions :numeric-fluents :durative-actions :action-costs)
  
  (:types
    location vehicle package - object
    truck airplane ship - vehicle
  )
  
  (:predicates
    (at ?obj - (either vehicle package) ?loc - location)
    (in ?pkg - package ?veh - vehicle)
    (road_route ?l1 ?l2 - location)
    (flight_route ?l1 ?l2 - location)
    (sea_route ?l1 ?l2 - location)
    (delivered ?p - package ?l - location)
  )
  
  (:functions
    (distance ?l1 ?l2 - location)
    (speed ?v - vehicle)
    (total-cost)
  )
  
  (:durative-action load
    :parameters (?p - package ?v - vehicle ?l - location)
    :duration (= ?duration 2)
    :condition (and
      (over all (at ?v ?l))
      (at start (at ?p ?l))
    )
    :effect (and
      (at start (not (at ?p ?l)))
      (at end (in ?p ?v))
      (at end (increase (total-cost) 5))
    )
  )
  
  (:durative-action unload
    :parameters (?p - package ?v - vehicle ?l - location)
    :duration (= ?duration 2)
    :condition (and
      (over all (at ?v ?l))
      (at start (in ?p ?v))
    )
    :effect (and
      (at start (not (in ?p ?v)))
      (at end (at ?p ?l))
      (at end (increase (total-cost) 5))
    )
  )
  
  (:durative-action drive
    :parameters (?t - truck ?l1 - location ?l2 - location)
    :duration (= ?duration (/ (distance ?l1 ?l2) (speed ?t)))
    :condition (and
      (at start (at ?t ?l1))
      (over all (road_route ?l1 ?l2))
    )
    :effect (and
      (at start (not (at ?t ?l1)))
      (at end (at ?t ?l2))
      (at end (increase (total-cost) (* (distance ?l1 ?l2) 2)))
    )
  )
  
  (:durative-action fly
    :parameters (?a - airplane ?l1 - location ?l2 - location)
    :duration (= ?duration (/ (distance ?l1 ?l2) (speed ?a)))
    :condition (and
      (at start (at ?a ?l1))
      (over all (flight_route ?l1 ?l2))
    )
    :effect (and
      (at start (not (at ?a ?l1)))
      (at end (at ?a ?l2))
      (at end (increase (total-cost) (* (distance ?l1 ?l2) 10)))
    )
  )
  
  (:durative-action sail
    :parameters (?s - ship ?l1 - location ?l2 - location)
    :duration (= ?duration (/ (distance ?l1 ?l2) (speed ?s)))
    :condition (and
      (at start (at ?s ?l1))
      (over all (sea_route ?l1 ?l2))
    )
    :effect (and
      (at start (not (at ?s ?l1)))
      (at end (at ?s ?l2))
      (at end (increase (total-cost) (* (distance ?l1 ?l2) 1)))
    )
  )

  (:durative-action mark-delivered
    :parameters (?p - package ?l - location)
    :duration (= ?duration 0.001)
    :condition (and
      (over all (at ?p ?l))
    )
    :effect (and
      (at end (delivered ?p ?l))
    )
  )
)