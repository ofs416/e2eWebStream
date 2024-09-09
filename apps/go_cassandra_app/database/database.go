package database

import (
	"log"

	"github.com/gocql/gocql"
)

var Session *gocql.Session

func Init() {
	cluster := gocql.NewCluster("cassandra")
	cluster.Keyspace = "sparkstreams"
	cluster.Consistency = gocql.Quorum
	var err error
	Session, err = cluster.CreateSession()
	if err != nil {
		log.Fatalf("Failed to connect to Cassandra: %v", err)
	}
}
