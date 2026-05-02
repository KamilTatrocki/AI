(define (problem sprzatanie-pokoi)
  (:domain robot-sprzatacz)
  
  (:objects
    robot1 - robot
    pokoj1 pokoj2 pokoj3 - room
  )

  (:init
    (at robot1 pokoj1)
    (dirty pokoj1)
    (dirty pokoj2)
    (dirty pokoj3)
  )

  (:goal
    (and 
      (clean pokoj1)
      (clean pokoj2)
      (clean pokoj3)
    )
  )
)