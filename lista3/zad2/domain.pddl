(define (domain robot-sprzatacz)
  (:requirements :typing)
  (:types robot room)
  
  (:predicates
    (at ?r - robot ?p - room)
    (dirty ?p - room)
    (clean ?p - room)
  )

  (:action move
    :parameters (?r - robot ?from - room ?to - room)
    :precondition (at ?r ?from)
    :effect (and (not (at ?r ?from)) (at ?r ?to))
  )

  (:action clean
    :parameters (?r - robot ?p - room)
    :precondition (and (at ?r ?p) (dirty ?p) (not (clean ?p)))
    :effect ( and (not (dirty ?p)) (clean ?p))
  )
)