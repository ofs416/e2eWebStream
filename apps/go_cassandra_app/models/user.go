package models

import "github.com/gocql/gocql"

type User struct {
	ID               gocql.UUID `form:"id"`
	FirstName        string     `form:"firstname"`
	LastName         string     `form:"lastname"`
	Gender           string     `form:"gender"`
	Address          string     `form:"address"`
	Postcode         string     `form:"postcode"`
	Email            string     `form:"email"`
	Username         string     `form:"username"`
	RegistrationDate string     `form:"registrationdate"`
	Phone            string     `form:"phone"`
	Picture          string     `form:"picture"`
}
