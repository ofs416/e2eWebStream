package main

import (
	"go_cassandra_app/controllers"
	"go_cassandra_app/database"
	"log"

	"github.com/gin-gonic/gin"
)

func main() {
	router := gin.Default()
	router.LoadHTMLGlob("templates/*")

	database.Init()

	router.GET("/", controllers.ListUsers)
	router.GET("/user/new", controllers.ShowUserForm)
	router.POST("/user/new", controllers.CreateUser)
	router.GET("/user/:id", controllers.ShowUserForm)
	router.POST("/user/:id", controllers.UpdateUser)
	router.POST("/user/:id/delete", controllers.DeleteUser)

	if err := router.Run(":8081"); err != nil {
		log.Fatalf("Failed to run server: %v", err)
	}
}
