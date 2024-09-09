package controllers

import (
	"go_cassandra_app/database"
	"go_cassandra_app/models"
	"log"
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/gocql/gocql"
)

func ListUsers(c *gin.Context) {
	var users []models.User
	iter := database.Session.Query("SELECT id, firstname, lastname, gender, address, postcode, email, username, registrationdate, phone, picture FROM sparkstreams.createdusers").Iter()
	var user models.User
	for iter.Scan(&user.ID, &user.FirstName, &user.LastName, &user.Gender, &user.Address, &user.Postcode, &user.Email, &user.Username, &user.RegistrationDate, &user.Phone, &user.Picture) {
		users = append(users, user)
	}
	if err := iter.Close(); err != nil {
		log.Printf("Error closing iterator: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.HTML(http.StatusOK, "index.html", gin.H{"users": users})
}

func ShowUserForm(c *gin.Context) {
	var user models.User
	if id := c.Param("id"); id != "" {
		if err := database.Session.Query("SELECT id, firstname, lastname, gender, address, postcode, email, username, registrationdate, phone, picture FROM sparkstreams.createdusers WHERE id = ?", id).Scan(
			&user.ID, &user.FirstName, &user.LastName, &user.Gender, &user.Address, &user.Postcode, &user.Email, &user.Username, &user.RegistrationDate, &user.Phone, &user.Picture); err != nil {
			log.Printf("Error fetching user with id %s: %v", id, err)
			c.JSON(http.StatusNotFound, gin.H{"error": "User not found"})
			return
		}
	}
	c.HTML(http.StatusOK, "user.html", gin.H{"user": user})
}

func CreateUser(c *gin.Context) {
	var user models.User
	if err := c.ShouldBind(&user); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	user.ID = gocql.TimeUUID()
	if err := database.Session.Query(
		"INSERT INTO sparkstreams.createdusers (id, firstname, lastname, gender, address, postcode, email, username, registrationdate, phone, picture) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
		user.ID, user.FirstName, user.LastName, user.Gender, user.Address, user.Postcode, user.Email, user.Username, user.RegistrationDate, user.Phone, user.Picture).Exec(); err != nil {
		log.Printf("Error inserting user: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.Redirect(http.StatusFound, "/")
}

func UpdateUser(c *gin.Context) {
	id := c.Param("id")
	var user models.User
	if err := c.ShouldBind(&user); err != nil {
		log.Printf("Error binding user data: %v", err)
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	if err := database.Session.Query("UPDATE sparkstreams.createdusers SET firstname = ?, lastname = ?, gender = ?, address = ?, postcode = ?, email = ?, username = ?, registrationdate = ?, phone = ?, picture = ? WHERE id = ?",
		user.FirstName, user.LastName, user.Gender, user.Address, user.Postcode, user.Email, user.Username, user.RegistrationDate, user.Phone, user.Picture, id).Exec(); err != nil {
		log.Printf("Error updating user with id %s: %v", id, err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.Redirect(http.StatusFound, "/")
}

func DeleteUser(c *gin.Context) {
	id := c.Param("id")
	if err := database.Session.Query("DELETE FROM sparkstreams.createdusers WHERE id = ?", id).Exec(); err != nil {
		log.Printf("Error deleting user with id %s: %v", id, err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.Redirect(http.StatusFound, "/")
}
