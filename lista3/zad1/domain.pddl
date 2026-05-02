(define (domain transport-domain)
  (:requirements :typing :durative-actions :numeric-fluents :action-costs :negative-preconditions)
  (:types
    location vehicle package - object
    truck airplane ship - vehicle
  )
  (:predicates
    (at ?obj - (either vehicle package) ?loc - location)
    (in ?pkg - package ?veh - vehicle)
    (connected-road ?l1 ?l2 - location)
    (connected-air ?l1 ?l2 - location)
    (connected-water ?l1 ?l2 - location)
  )
  (:functions
    (distance ?l1 ?l2 - location)
    (speed ?v - vehicle)
    (fuel-cost ?v - vehicle)
    (total-cost)
  )

  (:durative-action load
    :parameters (?v - vehicle ?p - package ?l - location)
    :duration (= ?duration 5)
    :condition (and
      (at start (at ?v ?l))
      (at start (at ?p ?l))
    )
    :effect (and
      (at start (not (at ?p ?l)))
      (at end (in ?p ?v))
      (at end (increase (total-cost) 10))
    )
  )

  (:durative-action unload
    :parameters (?v - vehicle ?p - package ?l - location)
    :duration (= ?duration 5)
    :condition (and
      (at start (at ?v ?l))
      (at start (in ?p ?v))
    )
    :effect (and
      (at start (not (in ?p ?v)))
      (at end (at ?p ?l))
      (at end (increase (total-cost) 10))
    )
  )

  (:durative-action drive-truck
    :parameters (?t - truck ?l1 ?l2 - location)
    :duration (= ?duration (/ (distance ?l1 ?l2) (speed ?t)))
    :condition (and
      (at start (at ?t ?l1))
      (over all (connected-road ?l1 ?l2))
    )
    :effect (and
      (at start (not (at ?t ?l1)))
      (at end (at ?t ?l2))
      (at end (increase (total-cost) (* (distance ?l1 ?l2) (fuel-cost ?t))))
    )
  )

  (:durative-action fly-airplane
    :parameters (?a - airplane ?l1 ?l2 - location)
    :duration (= ?duration (/ (distance ?l1 ?l2) (speed ?a)))
    :condition (and
      (at start (at ?a ?l1))
      (over all (connected-air ?l1 ?l2))
    )
    :effect (and
      (at start (not (at ?a ?l1)))
      (at end (at ?a ?l2))
      (at end (increase (total-cost) (* (distance ?l1 ?l2) (fuel-cost ?a))))
    )
  )

  (:durative-action sail-ship
    :parameters (?s - ship ?l1 ?l2 - location)
    :duration (= ?duration (/ (distance ?l1 ?l2) (speed ?s)))
    :condition (and
      (at start (at ?s ?l1))
      (over all (connected-water ?l1 ?l2))
    )
    :effect (and
      (at start (not (at ?s ?l1)))
      (at end (at ?s ?l2))
      (at end (increase (total-cost) (* (distance ?l1 ?l2) (fuel-cost ?s))))
    )
  )
)