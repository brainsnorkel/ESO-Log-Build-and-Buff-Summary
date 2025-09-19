"""
GraphQL queries for ESO Logs API.

This module contains the GraphQL queries needed to fetch trial rankings,
encounter details, and player build information.
"""

# GraphQL query to get top reports for a specific zone
GET_TOP_REPORTS_QUERY = """
query GetTopReports($zoneID: Int!, $limit: Int!, $page: Int!) {
  reportData {
    reports(
      zoneID: $zoneID
      limit: $limit
      page: $page
    ) {
      data {
        code
        title
        startTime
        endTime
        zone {
          id
          name
        }
        guild {
          name
        }
        fights {
          id
          name
          difficulty
          kill
          percentage
          startTime
          endTime
        }
      }
      total
      per_page
      current_page
      last_page
    }
  }
}
"""

# GraphQL query to get detailed fight information including players and gear
GET_FIGHT_DETAILS_QUERY = """
query GetFightDetails($code: String!, $fightIDs: [Int]!) {
  reportData {
    report(code: $code) {
      code
      title
      fights(fightIDs: $fightIDs) {
        id
        name
        difficulty
        kill
        percentage
        startTime
        endTime
        
        # Get all players in this fight
        playerDetails {
          name
          id
          server
          type
          specs {
            spec
            role
          }
        }
        
        # Get gear information for each player
        table(
          dataType: Summary
          hostilityType: Friendlies
        )
      }
    }
  }
}
"""

# GraphQL query to get player gear details
GET_PLAYER_GEAR_QUERY = """
query GetPlayerGear($code: String!, $fightID: Int!, $playerID: Int!) {
  reportData {
    report(code: $code) {
      fights(fightIDs: [$fightID]) {
        playerDetails(playerID: $playerID) {
          combatantInfo {
            gear {
              id
              slot
              quality
              icon
              name
              itemLevel
              bonusIDs
              gems
              enchant
              setID
              setName
              setPieces
            }
          }
        }
      }
    }
  }
}
"""

# GraphQL query to get zone rankings (for finding top performing groups)
GET_ZONE_RANKINGS_QUERY = """
query GetZoneRankings($zoneID: Int!, $difficulty: Int!, $size: Int!, $page: Int!, $limit: Int!) {
  worldData {
    encounter(id: $zoneID) {
      characterRankings(
        difficulty: $difficulty
        size: $size
        page: $page
        limit: $limit
        metric: dps
      ) {
        data {
          name
          class
          spec
          amount
          report {
            code
            startTime
          }
          guild {
            name
          }
        }
        total
        page
        hasMorePages
      }
    }
  }
}
"""
